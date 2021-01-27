"""
Created on Fri May 22 14:18:11 2020

@author: sasha
"""
from threading import Thread, Lock

from h5py import File
import numpy as np
import time
import json
import logging

from fridge.influxLog import setupDatabase, logToInflux

from instruments.cryocon import Cryocon
from instruments.bkpowersupply import BKPowerSupply
from instruments.compressor import CP2800
from instruments.pressure import ADS1115

def LogToConsole(Temps,State=None,Pressure=None,logStateOnly=False):
    #print data to console, if logging isn't available
    if not logStateOnly:
        logging.debug(Temps)
    if State is not None:
        logging.debug(State)


class FridgeThread(Thread):
    def __init__(self,fridge,lock):
        Thread.__init__(self)
        self.exit = False
        self.lock = lock
        self.fridge = fridge
        self.last_logupdate = time.time()
        self.last_state_logupdate = time.time()
        self.cycle_finished_time = None
        
        self.logging_interval = self.fridge.logging_interval
        
        self.state_dict = {"START": self.cycle_start,
                           "WAIT FOR HS": self.cycle_switches_desorb,
                           "DESORB": self.cycle_desorb,
                           "CONDENSE": self.cycle_condense,
                           "PUMP": self.cycle_pump,
                           "RUNNING": self.cycle_run,
                           "COOLDOWN": self.cooldown,
                           "WARMUP": self.warmup,"HEATING":self.warmup_heated}

        self.subroutines = {'NONE':None,'RECYCLE':'START','THERMALIZE':'COOLDOWN'}
    
    def cycle_start(self):
        logging.info("Started Cycling fridge.")
        self.start_time = time.time()
        self.fridge.set_heatswitch("pump_hs", False)
        self.fridge.set_heatswitch("1k_hs", True)
        logging.info("Waiting for heat switches to switch")
        #self.fridge.automation_state = "WAIT FOR HS"
        self.fridge.set_automation_state('WAIT FOR HS')

    def cycle_switches_desorb(self):
        if (time.time() - self.start_time > self.fridge.cycle_parameters["switch_time"]) or (
                    self.fridge.get_temperature('pump_hs') < self.fridge.cycle_parameters["pump_hs_off_temp"]):
            logging.info("Desorbing pump at : %f A @ %f V" % (
                self.fridge.cycle_parameters["desorb_current"], self.fridge.cycle_parameters["desorb_voltage"]))
            self.fridge.set_heater_current("pump_heater", self.fridge.cycle_parameters["desorb_current"])
            self.fridge.set_heater_voltage("pump_heater", self.fridge.cycle_parameters["desorb_voltage"])
            self.fridge.set_heater_output("pump_heater", True)
            self.fridge.set_automation_state("DESORB")

    def cycle_desorb(self):
        if (self.fridge.get_temperature('pump') > self.fridge.cycle_parameters["desorb_temp"]) or (
                        time.time() - self.start_time > self.fridge.cycle_parameters["desorb_time"] +
                    self.fridge.cycle_parameters["switch_time"]):
            logging.info("Finished desorbing. Waiting for helium to condense.")
            self.desorb_finished_time = time.time()
            self.fridge.set_automation_state("CONDENSE")
            self.fridge.set_heater_current("pump_heater", 0)
            self.fridge.set_heater_voltage("pump_heater", 0)
            self.fridge.set_heater_output("pump_heater", False)

    def cycle_condense(self):
        if time.time() - self.desorb_finished_time > self.fridge.cycle_parameters["condense_time"]:
            logging.info("Finished Condensing. Waiting for 1K HS to shut off.")
            self.fridge.set_heatswitch("1k_hs", False)
            self.condense_finished_time = time.time()
            self.fridge.set_automation_state("PUMP")

    def cycle_pump(self):
        if time.time() - self.condense_finished_time > self.fridge.cycle_parameters["switch_time"]:
            logging.info("Turning on the adsorption pump.")
            self.fridge.set_heatswitch("pump_hs", True)
            self.fridge.set_automation_state("RUNNING")
            self.cycle_finished_time = time.time()

    def cycle_run(self):
        #wait for 1k pot thermalization
        if (self.cycle_finished_time is None) or (time.time() - self.cycle_finished_time > self.fridge.cycle_parameters["switch_time"]):
            #check that cycle has ended
            if self.fridge.get_temperature('1k_pot') > self.fridge.cfg['successful_cycle_threshold']:
                #cycle finished
                logging.info('cycle finished')
                if self.fridge.subroutine_state != 'NONE':
                    logging.info(self.fridge.subroutine_state)
                    self.fridge.set_automation_state(self.subroutines[self.fridge.subroutine_state])
                else:
                    #cycle finished, but no automation specified
                    self.fridge.automation_state = None

    def cooldown(self):
        if not self.fridge.get_heatswitch_state("pump_hs"):
            self.fridge.set_heatswitch("pump_hs", True)
        if not self.fridge.get_heatswitch_state("1k_hs"):
            self.fridge.set_heatswitch("1k_hs", True)
        #self.fridge.automation_state = None

    def warmup(self):
        #check that cycle has ended
        if self.fridge.get_temperature('pump') > self.fridge.cfg['warmup_parameters']['Warm_temp']:
            #finished actively warming, turn off automation
            self.fridge.automation_state = None
            self.fridge.set_heater_current("pump_heater", 0)
            self.fridge.set_heater_voltage("pump_heater", 0)
            self.fridge.set_heater_output("pump_heater", False)
            
    def warmup_heated(self):
        #turn off compressor
        
        #turn heatswitch heaters to warmup values
        self.fridge.switch_states['pump_hs'] = True
        self.fridge.set_heater_voltage('pump_hs', self.fridge.cfg['warmup_parameters']['V_pump_hs'])
        self.fridge.set_heater_current('pump_hs', self.fridge.cfg['warmup_parameters']['I_pump_hs'])
        self.fridge.set_heater_output('pump_hs', True)
        
        time.sleep(0.1)
        self.fridge.switch_states['1k_hs'] = True
        self.fridge.set_heater_voltage('1k_hs', self.fridge.cfg['warmup_parameters']['V_1k_hs'])
        self.fridge.set_heater_current('1k_hs', self.fridge.cfg['warmup_parameters']['I_1k_hs'])
        
        time.sleep(0.1)
        self.fridge.set_heater_output('1k_hs', True)
        self.fridge.set_heater_voltage('pump_heater', self.fridge.cfg['warmup_parameters']['V_pump'])
        self.fridge.set_heater_current('pump_heater', self.fridge.cfg['warmup_parameters']['I_pump'])
        self.fridge.set_heater_output('pump_heater', True)
        
        #start monitoring temperature
        self.fridge.set_automation_state("WARMUP")
        
    
    def run(self):
        try:
            while not self.exit:
                if self.fridge.automation_state is not None:
                    self.state_dict[self.fridge.automation_state]()
                if time.time() - self.last_logupdate > self.logging_interval:
                    #time to update log
                    #check if state changed or 10 log updates have passed
                    if self.fridge.state_changed_flag or time.time() - self.last_state_logupdate > 10*self.logging_interval:
                        self.fridge.update_log(logStateOnly=self.fridge.logStateOnly,logAutomationState=True)
                        self.fridge.state_changed_flag=False
                        self.last_state_logupdate = time.time()
                    else:
                        self.fridge.update_log(logStateOnly=self.fridge.logStateOnly)
                    self.last_logupdate = time.time()
                    
                time.sleep(0.5)
                
        except KeyboardInterrupt:
            logging.warn('Keyboard Interrupt (Ctrl-C)')


class SlabFridge():
    def __init__(self,configfile,useInflux=False,logStateOnly=False,lock=False):
        self.useInflux = useInflux
        
        if self.useInflux:
            self.client = setupDatabase()
        
        self.logStateOnly=logStateOnly
        
        self.automation_state=None
        self.subroutine_state='NONE'
        
        self.state_changed_flag = False
        
        with open(configfile, 'r') as fid:
            cfg = json.loads(fid.read())

        self.cfg = cfg
        self.logging_interval = self.cfg['logging_parameters']['logging_interval']

        self.__dict__.update(cfg)
        
        '''
        for inst, info in cfg['instruments'].items():
            self.__dict__[inst] = getattr(slab.instruments, info['class'])(name=inst, address=info['address'])
        '''
        # Import instruments
        self.ps = BKPowerSupply(name='bkp') #note: during power outage BKP will be powered off
        self.monitor = Cryocon(name='monitor')
        try:
            self.compressor = CP2800(name='compressor')
        except Exception:
            self.compressor = None
            logging.warn('Could not load compressor')
        try:
            self.pressure = ADS1115()
        except Exception:
            self.pressure = None
            logging.warn('Could not connect to pressure guage')
            
        #current switch state storage    
        self.switch_states = {'pump_hs':False,'1k_hs':False}
        
        #setup current temperature variable
        self.temperatures = {}
        for name, ch in self.cfg['thermometers'].items():
            self.temperatures[name] = 0.0
        
        #current pressure
        self.current_pressure = None
        
        logging.debug('cold start ? %s', self.cfg['forceResetOnStart'])
        if self.cfg['forceResetOnStart']:
            #force reset all channels
            logging.info('resetting channels')
            
            for heater, ch in self.cfg['heater_chs'].items():
                self.set_heater_current(heater, 0)
                time.sleep(.1)
                self.set_heater_voltage(heater, 0)
                time.sleep(.1)
                self.ps.set_output(True, channel=ch)
                time.sleep(.1)

        for hs in list(self.cfg["heatswitch_voltages"].keys()):
            #self.set_heatswitch(hs, False)
            #check the current heater status
            logging.debug('%s is %s',hs,self.get_heater_voltage(hs)>0.5)
            self.switch_states[hs] = self.get_heater_voltage(hs)>0.5
        
        if not self.cfg['forceResetOnStart']:
            if (self.get_temperature('1k_pot') < self.cfg['successful_cycle_threshold']) and (self.get_temperature('1k_pot') > 0):
                logging.info('Cycle hold in progress. Resuming automation...')
                self.automation_state="RUNNING"

            
    def update_log(self,logStateOnly=False,logAutomationState=False):
        self.update_temperatures()
        self.update_pressure()
        if self.useInflux:
            if logAutomationState and self.automation_state is not None:
                logToInflux(self.get_temperatures(),client=self.client,State = self.automation_state,Pressure=self.get_pressure_data())
            else:
                logToInflux(self.get_temperatures(),client=self.client,Pressure=self.get_pressure_data())
        #write to console
        #LogToConsole(self.TempKeys, [t[self.index] for t in self.TemplateData],State=self.stateChanges.get(self.index,None),logStateOnly=logStateOnly)

    def stop_automation(self):
        self.automation_state = None
        #turn off pump heater
        self.set_heater_current("pump_heater", 0)
        self.set_heater_voltage("pump_heater", 0)
        self.set_heater_output("pump_heater", False)

    def set_automation_state(self,state):
        if state in self.automation_thread.state_dict.keys():
            self.automation_state = state
            self.state_changed_flag = True
        
    def get_automation_state(self):
        return self.automation_state

    def get_subroutine_state(self):
        #print(self.subroutine_state)
        return self.subroutine_state

    def set_subroutine_state(self,state):
        if state in self.automation_thread.subroutines.keys():
            logging.info('automation subroutine set to: %s',state)
            self.subroutine_state = state

    def set_heatswitch(self, name, state=False):
        self.switch_states[name] = state
        if state:
            self.set_heater_voltage(name, self.cfg['heatswitch_voltages'][name])
            self.set_heater_current(name, self.cfg['heatswitch_currents'][name])
        else:
            self.set_heater_voltage(name, 0)
            self.set_heater_current(name, 0)
        self.set_heater_output(name, state)

    def get_heatswitch_state(self, name):
        return self.switch_states[name]
    
    def get_heatswitch_states(self):
        return self.switch_states

    #unused?
    def get_heater_labels(self):
        return self.heater_labels

    #unused?
    def get_thermometer_labels(self):
        return self.thermometer_labels
    
    def get_temperatures(self):
        #return {f:t for f,t in zip(self.TempKeys,[t[self.index] for t in self.TemplateData])}
        d = {}
        for name, ch in self.cfg['thermometers'].items():
            d[name] = self.get_temperature(name)
        return d
        
    def get_temperature(self, name):
        try:
            return self.temperatures[name]
        except:
            return 0
        '''
        if name in self.TempKeys:
            return self.TemplateData[self.TempKeys.index(name)][self.index]
        else:
            return None
        '''
    def update_temperatures(self):
        for name, ch in self.cfg['thermometers'].items():
            self.update_temperature(name)   

    def update_temperature(self, name):
        #return self.get_temperature(name)
        #self.lock.acquire()
        temp = 0
        try:
            temp = self.monitor.get_temp(self.cfg['thermometers'][name])
        finally:
            #self.lock.release()
            pass
        self.temperatures[name]=temp
        
    def get_pressure(self):
        if self.current_pressure is not None:
            return [d['pressure'] for d in self.current_pressure]
        else:
            return None

    def get_pressure_data(self):
        if self.current_pressure is not None:
            return self.current_pressure
        else:
            return None
    
    def update_pressure(self):
        if self.pressure is not None:
            self.current_pressure = self.pressure.get_all_data()

    def set_heater_output(self, name, state):
        time.sleep(0.1)
        self.ps.set_output(True, channel=self.cfg['heater_chs'][name])

    def set_heater_current(self, name, value):
        time.sleep(0.1)
        self.ps.set_current(self.cfg['heater_chs'][name], value)

    def set_heater_voltage(self, name, value):
        time.sleep(0.1)
        self.ps.set_voltage(self.cfg['heater_chs'][name], value)

    def get_heater_voltage(self, name):
        return self.ps.get_voltage(self.cfg['heater_chs'][name])
        return 0

    def get_heater_current(self, name):
        return self.ps.get_current(self.cfg['heater_chs'][name])
        return 0
        

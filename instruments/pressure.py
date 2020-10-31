# -*- coding: utf-8 -*-
"""
Created on Sat Sep 05 08:47:30 2020

@author: Sasha

Uses ADS1x15 to query voltage on PX209 pressure transducer
"""
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

class ADSinstrument():
    # a sub-instrument class that runs under the ADS1115 umbrella class.
    # functions: 
    # scaled_voltage():
    #       Vmin (float): Voltage corresponding to 0
    #       Vmax (float): Voltage corresponding to 1
    # set_units(string:units)
    def __init__(self,name,Vmin=0.0,Vmax=5.0,Pmin=0.0,Pmax=1.0,units='None'):
        self.chan = None
        self.name = name
        self.Vmin = Vmin
        self.Vmax = Vmax
        self.Pmin = Pmin
        self.Pmax = Pmax
        self.set_units(units)

    def get_id(self):
        return str(self.name) + '(' + str(self.units) + ')'

    def set_chan(self,chan):
        self.chan = chan

    def set_units(self,units='None'):
        self.units = units
    
    def scaled_voltage(self,voltage):
        return ((voltage - self.Vmin) / (self.Vmax-self.Vmin))

    def calc_pressure(self,v_scaled):
        pressure = self.Pmin + v_scaled*(self.Pmax - self.Pmin)
        return pressure

    def get_voltage(self):
            return float(self.chan.voltage)
        
    def get_pressure(self):
        return self.calc_pressure(self.scaled_voltage(self.get_voltage()))

    def get_data(self):
        voltage = self.get_voltage()
        return {'pressure':self.calc_pressure(self.scaled_voltage(voltage)),'voltage':voltage,'units':self.units}

class PX209(ADSinstrument):
    def __init__(self,Vmin=-0.02,Vmax=-5.0,units='barAbs'):
        super().__init__('PX209',Vmin,Vmax,units=units)
    
    def set_units(self,units='psi'):
        super().set_units(units)
        if units is 'psi':
            self.Pmax = (135.0+14.7346)
            self.Pmin = -14.7346
        elif units is 'barRel':
            self.Pmax = (9.30792+1.01952)
            self.Pmin = -1.01952
        elif units is 'barAbs':
            self.Pmax = (9.30792+1.01952)
            self.Pmin = 0.0


class TPG251(ADSinstrument):
    def __init__(self,Vmin=-0.0,Vmax=-5.0,units='Bar',sci_format=False):
        super().__init__('TPG251',Vmin,Vmax,units=units)
        self.sci_format=sci_format
    
    def set_units(self,units='mBar'):
        super().set_units(units)
        #assume Pmin =10^-d
        if units is 'mBar':
            self.Pmin = pow(10,-11.33)
        elif units is 'Bar':
            self.Pmin = pow(10,-14.33)

    def calc_pressure(self,v_scaled):
        pressure = pow(10,1.667*max(min(v_scaled*10,8.596289),1.817020))*self.Pmin
        if self.sci_format:
            return format(pressure,'4.6e')
        else:
            return pressure



class ADS1115():
    
    def __init__(self,name='ADS1115',gain=2/3,differential=True,modules=[PX209(),TPG251()]):
        #configure ADS settings
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.ads = ADS.ADS1115(self.i2c)
        self.ads.gain = 2/3
        #configure input channels
        if differential:
            self.chan = [AnalogIn(self.ads, ADS.P0, ADS.P1),AnalogIn(self.ads, ADS.P2, ADS.P3)]
        else:
            self.chan = [AnalogIn(self.ads, ADS.P0),AnalogIn(self.ads, ADS.P1),AnalogIn(self.ads, ADS.P2),AnalogIn(self.ads, ADS.P3)]
        self.modules = modules
        for i in range(min(len(self.modules),len(self.chan))):
            self.modules[i].set_chan(self.chan[i])
    
    def get_id(self):
        out = "ADS1115: "
        for module in self.modules:
            out = out + module.get_id()+" "
        return out

    def get_voltage(self,i=0):
        return self.modules[i].get_voltage()

    def get_pressure(self,i=0):
        return self.modules[i].get_pressure()

    def get_data(self,i=0):
        return self.modules[i].get_data()
    
    def get_voltages(self):
        return [module.get_voltage() for module in self.modules]

    def get_pressures(self):
        return [module.get_pressure() for module in self.modules]

    def get_all_data(self):
        return [module.get_data() for module in self.modules]
 

if __name__=="__main__":
    p=ADS1115()
    print(p.get_id())
    print(p.get_all_data())
        
        

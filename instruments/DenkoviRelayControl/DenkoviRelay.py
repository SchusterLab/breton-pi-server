#!usr/bin/python3
'''
Written by aanferov - June 2021

A wrapper for mcp2200.py written by ctdx (https://github.com/cdtx/mcp2200.git)
Implements basic set/clear functions for 4 relay Denkovi Relay board, which uses GPIO pins 0-3 on MCP2200 chip
'''

from MCP2200 import MCP2200Device

class DenkoviRelayBoard(MCP2200Device):
    #note: eeprom commands from MCP2200Device class still exposed
    def __init__(self,deviceId=0,nChannels=4,relayNames=None):
        self.deviceId = deviceId
        self.nChannels=nChannels
        if relayNames is not None:
            self.relayNames = relayNames
            #limit channels to named relays
            self.nChannels = len(self.relayNames)
        else:
            self.relayNames = [str(i) for i in range(self.nChannels)]
        MCP2200Device.__init__(self)
        self.connect(deviceId=self.deviceId)
        if not self.dev:
            raise Exception('Could not connect to Relay Board')

        #read current outputs
        self.outputs = self.read_all()['IO_Port_Val_bmap']

    def get_name(self):
        return self.name

    def get_id(self):
        if not self.dev:
            return ''
        else:
            return self.dev.product

    def get_serial(self):
        if not self.dev:
            return ''
        else:
            return self.dev.serial_number

    #TODO wrap read / write functions in locks to prevent desync

    def set_baud_rate(self,BaudRateParam):
        ''' bool set_baud_rate(unsinged long BaudRateParam)'''
        config = self.read_all()
        baud_rate_divisor = (12000000//BaudRateParam) - 1
        Baud_H = baud_rate_divisor // 2**8
        Baud_L = baud_rate_divisor % (2**8)
        config['Baud_H'] = Baud_H
        config['Baud_L'] = Baud_L
        return self.device.configure(**config) 
        
    #Relay read functions
    def update_outputs(self):
        #updates self.outputs with current relay values
        self.outputs = self.read_all()['IO_Port_Val_bmap']
    
    def get_relay_state(self,index):
        #bool get_relay_state(unsigned int index)
        #reads tvalue of one pin
        if 0 <= index <= self.nChannels-1:
            self.update_outputs()
            return (1 if self.outputs & (1<<index) else 0)
        else:
            return -1

    def get_relay_states(self):
        #[bool] get_relay_states()
        #returns list of boolean values corresponding to relay state

        self.update_outputs()
        return [(1<<index & self.outputs)>0 for index in range(self.nChannels)]

    def get_relay_dict(self):
        #dict get_relay_dict()
        #queries then returns a dictionary with relay names + relay values

        self.update_outputs()
        return {self.relayNames[index]:(1<<index & self.outputs)>0 for index in range(self.nChannels)}
            
    #Relay set functions
    def set_relay_on(self,index):
        #bool set_relay(unsigned int index)
        #turns on a single relay
        #returns True if successful
        
        if index < 0 or index > self.nChannels-1:
            return False
        bitmap = 1<<index
        self.set_clear_outputs(**{'Set_bmap':bitmap,'Clear_bmap':0})
        return True

    def set_relay_off(self,index):
        #bool relay_off(unsigned int index)
        #turns off a single relay
        #returns True if successful
        
        if index < 0 or index > self.nChannels-1:
            return False
        bitmap = 1<<index
        self.set_clear_outputs(**{'Set_bmap':0,'Clear_bmap':bitmap})
        return True

    def set_relay(self,index,value):
        #bool set_relay(unsigned int index, bool value)
        #turns relay to value
        #returns True if successful
        
        if value:
            return self.set_relay_on(index)
        else:
            return self.set_relay_off(index)

    def set_relay_by_name(self,name,value):
        #bool set_relay_by_name(string name, bool value)
        #grabs relay index by name from self.relayNames, and sets it to value
        #returns True if successful
        
        index = self.relayNames.index(name)
        return self.set_relay(index,value)

    def clear_all(self,nChannels=4):
        #bool clear_all(*unsigned int nChannel)
        #turns all relays off, regardless of how many channels are defined
        self.set_clear_outputs(**{'Set_bmap':0,'Clear_bmap':168}) 


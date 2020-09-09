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

class PX209():
    
    def __init__(self,name='PX209',gain=2/3,Vmin=0.04,Vmax=5.0,units='barAbs'):
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.ads = ADS.ADS1115(self.i2c)
        self.ads.gain = 2/3
        self.chan = AnalogIn(self.ads, ADS.P0, ADS.P1)
        #setup calibration
        self.Vmin = Vmin
        self.Vmax = Vmax
        self.set_units(units)
    
    def get_id(self):
        return "ADS1115"
    
    def get_voltage(self):
        return float(self.chan.voltage)
    
    def get_pressure(self,units='psi'):
        voltage = -1*self.get_voltage()
        Vscaled = ((voltage - self.Vmin) / self.Vmax)
        return (Vscaled*self.Pmax + self.Pmin)
    
    def set_units(self,units='psi'):
        if units is 'psi':
            self.Pmax = (135.0+14.7346)
            self.Pmin = -14.7346
        elif units is 'barRel':
            self.Pmax = (9.30792+1.01952)
            self.Pmin = -1.01952
        elif units is 'barAbs':
            self.Pmax = (9.30792+1.01952)
            self.Pmin = 0.0
    
if __name__=="__main__":
    p=PX209(units='barAbs')
    print(p.get_id())
    print(p.get_voltage(),p.get_pressure())
        
        
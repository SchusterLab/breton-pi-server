#
import numpy as np
import time, serial, struct
from instruments.instruments import SerialInstrument

class RelayMCP2200(SerialInstrument):
    def __init__(self,name="",address='/dev/ttyACM0',enabled=True,baudrate=9600,timeout=0.25):
        SerialInstrument.__init__(self,name=name,address=address,enabled=enabled,timeout=timeout,baudrate=baudrate,recv_length=16)
        self.ser._bytesize = serial.EIGHTBITS
        self.ser._parity = serial.PARITY_NONE
        self.ser._stopbits = serial.STOPBITS_ONE



if __name__ == "__main__":
    relay = RelayMCP2200(address='/dev/ttyS3',enabled=True,baudrate=9600)
    print('initializing relay...')
    relay.ser.write(bytearray([int('0x80',16)]+[int('0x00',16)]*15 ))
    print(relay.ser.read(16))

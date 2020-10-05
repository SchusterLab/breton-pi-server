#starts compressor
from instruments.compressor import CP2800
import argparse

if __name__ == "__main__":
    cp = CP2800(address='/dev/ttyUSB0', baudrate=9600, timeout=0.1)
    parser = argparse.ArgumentParser()
    parser.add_argument('-s','--status',required=True,help='Target compressor status. \'on\' or \'off\'')
    s = parser.parse_args().status
    if s == 'on':
        if(cp.get_compressor_status()):
            print('compressor already on')
        else:
            print('starting compressor')
            cp.start_compressor()
    elif s == 'off':
        if not (cp.get_compressor_status()):
            print('compressor already off')
        else:
            print('stopping compressor')
            cp.stop_compressor()
    
    print(("The compressor status is now %d" % cp.get_compressor_status()))
#!/usr/bin/python3
from instruments.DenkoviRelayControl.DenkoviRelay import DenkoviRelayBoard
import time
import argparse


if __name__ == "__main__":
    relay = DenkoviRelayBoard()
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    #parser.add_argument('-s','--status',required=False,help='Target valve status. \'on\', \'off\', or \'pulse\'')
    group.add_argument('-on',action='store_true',help='Turns ON n2 solenoid')
    group.add_argument('-off',action='store_true',help='Turns OFF n2 solenoid')
    group.add_argument('-pulse',action='store_true',help='Pulses n2 solenoid for [time]s')
    parser.add_argument('-t','--time',required=False,help='Pulse duration in s (default 2.0)',type=float)
    args = parser.parse_args()
    
    t = args.time
    if t is None:
        t = 2.0
    
    if args.on:
        relay.set_relay_on(3)
        print('Turning ON n2')
    elif args.off:
        relay.set_relay_off(3)
        print('Turning OFF n2')
    elif args.pulse:
        print('Pulsing n2 for %ds'%t)
    
        relay.set_relay_on(3)
        #sleep for 2s
        for i in range(20):
            time.sleep(t/20)
        relay.set_relay_off(3)

#!/usr/bin/python3
from instruments.DenkoviRelayControl.DenkoviRelay import DenkoviRelayBoard
import time
import argparse


if __name__ == "__main__":
    relay = DenkoviRelayBoard()
    parser = argparse.ArgumentParser()
    parser.add_argument('-ch','--channel',required=True,help='Heater channel. \'pump\' or \'heater\'')
    action_group = parser.add_mutually_exclusive_group()
    #parser.add_argument('-s','--status',required=False,help='Target valve status. \'on\', \'off\', or \'pulse\'')
    action_group.add_argument('-on',action='store_true',help='Turns ON n2 solenoid')
    action_group.add_argument('-off',action='store_true',help='Turns OFF n2 solenoid')
    action_group.add_argument('-pulse',action='store_true',help='Pulses n2 solenoid for [time]s')
    parser.add_argument('-t','--time',required=False,help='Pulse duration in s (default 2.0)',type=float)
    args = parser.parse_args()
    
    t = args.time
    if t is None:
        t = 2.0
        
    index = None
    if args.channel == 'pump':
        index = 0
    elif args.channel == 'heater':
        index = 1

    if index is not None:
        if args.on:
            relay.set_relay_on(index)
            print('Turning ON ch%d'%index)
        elif args.off:
            relay.set_relay_off(index)
            print('Turning OFF ch%d'%index)
        elif args.pulse:
            print('Pulsing %s for %ds'%(index,t))
        
            relay.set_relay_on(index)
            #sleep for 2s
            for i in range(20):
                time.sleep(t/20)
            relay.set_relay_off(index)
    else:
        print('Incorrect channel!')

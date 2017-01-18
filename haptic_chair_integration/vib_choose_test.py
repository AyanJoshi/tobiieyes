import os
import glob
import sys
import time
import serial
import logging
import random

logging.basicConfig(level=logging.DEBUG)

from pyhaptic import HapticInterface

def find_comm_port():
    comm_port = []
    if os.name == 'posix':
        comm_port = glob.glob('/dev/tty.*')
        comm_port.extend( glob.glob('/dev/ttyACM*'))
        comm_port.extend( glob.glob('/dev/ttyUSB*'))
    elif os.name == 'nt':
        available = []
        for i in range(256):
            try:
                s = serial.Serial(i)
                available.append('COM'+str(i + 1))
                s.close()
            except serial.SerialException:
                pass
        comm_port.extend(available)
    print "Printing current available comm ports.\n"
    if len(comm_port) == 1:
        return comm_port[0]
    for i in comm_port:
        print i
    comm_choice = raw_input("\nPlease choose the full path to the comm port that the haptic controller is connected to:")
    return comm_choice



if __name__ == '__main__':

    two_d_display = HapticInterface(find_comm_port())
    try:
        two_d_display.connect()
    except:
        print "Failed to connect on ..."
        sys.exit(1)

    print "enter a number 0-9 to activate that function"
    print "anything else to exit"
    while True:
        comm_choice = sys.stdin.read(1)
        sys.stdin.read(1) #dump the newline char
        two_d_display.vibrate(0,int(comm_choice),0,1)

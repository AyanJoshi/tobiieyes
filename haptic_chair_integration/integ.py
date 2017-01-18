'''
    Example for how to receive live data and display live video (without gaze overlay) from glasses.
    gstreamer 0.10 required in order to display live video.

    Note: This example program is *only* tested with Python 2.7 on Ubuntu 12.04 LTS
          and Ubuntu 14.04 LTS (running natively).
'''
import os
import glob
import sys
import time
import serial
import logging
import random
import time
import socket
import threading
import signal
import sys
import pygst

pygst.require('0.10')
import gst

# For Drawing 
import pygame

timeout = 1.0
running = True


# Output Screen Res
SCREEN_RES_X = 1000
SCREEN_RES_Y = 1000
HAPT_RES_X = 8
HAPT_RES_Y = 5

# Smoothing Factor
SF = 10

# GLASSES_IP = "fd93:27e0:59ca:16:76fe:48ff:fe05:1d43" # IPv6 address scope global
#GLASSES_IP = "10.46.16.86"  # IPv4 address
GLASSES_IP = "10.218.110.92"  # IPv4 address
PORT = 49152


# Keep-alive message content used to request live data and live video streams
KA_DATA_MSG = "{\"type\": \"live.data.unicast\", \"key\": \"some_GUID\", \"op\": \"start\"}"
KA_VIDEO_MSG = "{\"type\": \"live.video.unicast\", \"key\": \"some_other_GUID\", \"op\": \"start\"}"


# Gstreamer pipeline definition used to decode and display the live video stream
PIPELINE_DEF = "udpsrc do-timestamp=true name=src blocksize=1316 closefd=false buffer-size=5600 !" \
               "mpegtsdemux !" \
               "queue !" \
               "ffdec_h264 max-threads=0 !" \
               "ffmpegcolorspace !" \
               "xvimagesink name=video"


# Create UDP socket
def mksock(peer):
    iptype = socket.AF_INET
    if ':' in peer[0]:
        iptype = socket.AF_INET6
    return socket.socket(iptype, socket.SOCK_DGRAM)


# Callback function
def send_keepalive_msg(socket, msg, peer):
    while running:
        print("Sending " + msg + " to target " + peer[0] + " socket no: " + str(socket.fileno()) + "\n")
        socket.sendto(msg, peer)
        time.sleep(timeout)


def signal_handler(signal, frame):
    stop_sending_msg()
    sys.exit(0)


def stop_sending_msg():
    global running
    running = False

def avg(coord_list):
	summer = 0
	for c in coord_list:
		summer = summer + c
	return summer/len(coord_list)

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

if __name__ == "__main__":
    
    two_d_display = HapticInterface(find_comm_port())
    try:
        two_d_display.connect()
    except:
        print "Failed to connect on ..."
        sys.exit(1)

    signal.signal(signal.SIGINT, signal_handler)
    peer = (GLASSES_IP, PORT)

    # Create socket which will send a keep alive message for the live data stream
    data_socket = mksock(peer)
    td = threading.Timer(0, send_keepalive_msg, [data_socket, KA_DATA_MSG, peer])
    td.start()

    # Create socket which will send a keep alive message for the live video stream
    video_socket = mksock(peer)
    tv = threading.Timer(0, send_keepalive_msg, [video_socket, KA_VIDEO_MSG, peer])
    tv.start()

    # Create gstreamer pipeline and connect live video socket to it
    pipeline = None
    try:
        pipeline = gst.parse_launch(PIPELINE_DEF)
    except Exception, e:
        print e
        stop_sending_msg()
        sys.exit(0)

    src = pipeline.get_by_name("src")
    src.set_property("sockfd", video_socket.fileno())

    #pipeline.set_state(gst.STATE_PLAYING)

    # For drawing on screen
    red = (255,0,0)
    green = (0,255,0)
    blue = (0,0,255)
    darkBlue = (0,0,128)
    white = (255,255,255)
    black = (0,0,0)
    pink = (255,200,200)
    screen = pygame.display.set_mode((SCREEN_RES_X,SCREEN_RES_Y))
    screen.fill(white)

    x_smooth = [0]
    y_smooth = [0]
    motor = 0

    while running:
        # Read live data
        data, address = data_socket.recvfrom(1024)

	d_spl = data.split(',', 2)
	iden = d_spl[2].split(':')
	if(iden[0] == '"gp"'):
		g_coords = (iden[1].split(',', 2))
		cur_x = float((g_coords[0])[1:])
		cur_y = float((g_coords[1])[:-1])
		if((cur_x+cur_y) > 0.001):
			# Here we display to the screen the pupil position
			x_smooth.insert(0, cur_x)
			y_smooth.insert(0, cur_y)
			if(len(x_smooth) > SF):
				x_smooth.pop()
			if(len(y_smooth) > SF):
				y_smooth.pop()
			screen.fill(white)
			pygame.draw.circle(screen, green, (int(SCREEN_RES_X*avg(x_smooth)), int(SCREEN_RES_Y*avg(y_smooth))), 10, 3)
			pygame.display.update()
			motor = (HAPT_RES_X-int(avg(x_smooth)*HAPT_RES_X)) + int(avg(y_smooth)*HAPT_RES_Y)*HAPT_RES_X - 1
			two_d_display.vibrate(motor,4,0,3)
			print(g_coords[0] + ', ' + g_coords[1] + '\tMotor: ' + str(motor))
		

        state_change_return, state, pending_state = pipeline.get_state(0)

        if gst.STATE_CHANGE_FAILURE == state_change_return:
            stop_sending_msg()

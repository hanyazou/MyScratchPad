#!/usr/bin/python

#
# RYZE Tello toy drone SDK and PS3 joystick
#

import threading 
import socket
import time
import sys
import pygame
from pygame.locals import *

class buttons:
    UP = 4
    RIGHT = 5
    DOWN = 6
    LEFT = 7
    L2 = 8
    R2 = 9
    L1 = 10
    R1 = 11
    TRIANGLE = 12
    CIRCLE = 13
    CROSS = 14
    SQUARE = 15

class Tello:
    def __init__(self):
        self.debug = False
        self.cmd = None
        self.command('command')
        threading.Thread(target=self.thread).start()

    def command(self, cmd, repeat = True):
        if self.debug:
            print ('Tello.command(cmd=%s)' % cmd)
        if self.cmd != 'command' or cmd == 'quit':
            self.cmd = cmd
            self.repeat = repeat
        else:
            print ('Tello.command(cmd=%s): not ready' % cmd)

    def disableRepeat(self):
        if self.cmd != 'command':
            self.repeat = False

    def thread(self):
        # Create a UDP socket
        tello_addr = ('192.168.10.1', 8889)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        local_ddr = ('', 9000)
        sock.bind(local_ddr)
        sock.settimeout(3.0)

        while self.cmd != 'quit':
            cmd = self.cmd
            if self.debug:
                print ('Tello.thread(cmd=%s)' % cmd)
            if cmd == '' or cmd == None:
                time.sleep(0.01)
            else:
                try:
                    # Send data
                    if not self.debug:
                        sent = sock.sendto(cmd, tello_addr)
                except KeyboardInterrupt, e:
                    print('send: command=' + cmd + ': ')
                    print(e)
                    exit(1)
                except Exception, e:
                    print('send: command=' + cmd + ': ')
                    print(e)
                    time.sleep(3.0)
                    continue

                try:
                    if not self.debug:
                        data, server = sock.recvfrom(1518)
                    else:
                        data = 'OK'
                    print ('command: ' + cmd + ': ' + data)
                except socket.timeout, e:
                    print ('recv: cmd=' + cmd + ': timeout')
                    data = None
                except Exception, e:
                    print ('recv: cmd=' + cmd + ': ')
                    print(e)
                    data = None
                if self.cmd == 'command' and data == 'OK':
                    print('\nREADY\n')
                    self.cmd = None
                if not self.repeat:
                    print('end of command repeat: cmd=' + self.cmd)
                    self.cmd = None
                if data != 'OK':
                    time.sleep(0.2)

        print ('tello: exit from the thread.')

def main():
    pygame.init()
    pygame.joystick.init()
    try:
        js = pygame.joystick.Joystick(0)
        js.init()
        print 'Joystick name: ' + js.get_name()
    except pygame.error:
        print 'no joystick found'

    tello = Tello()

    while 1:
        try:
            time.sleep(0.01)  # loop with pygame.event.get() is too mush tight w/o some sleep
            for e in pygame.event.get():
                if e.type == pygame.locals.JOYAXISMOTION: # 7
                    x , y = js.get_axis(0), js.get_axis(1)
                    # print 'x and y : ' + str(x) +' , '+ str(y)
                elif e.type == pygame.locals.JOYBUTTONDOWN: # 10
                    if e.button == buttons.L2:
                        tello.command('takeoff')
                    elif e.button == buttons.L1:
                        tello.command('land')
                    elif e.button == buttons.UP:
                        tello.command('up 20')
                    elif e.button == buttons.DOWN:
                        tello.command('down 20')
                    elif e.button == buttons.RIGHT:
                        tello.command('cw 20')
                    elif e.button == buttons.LEFT:
                        tello.command('ccw 20')
                    elif e.button == buttons.TRIANGLE:
                        tello.command('forward 20')
                    elif e.button == buttons.CROSS:
                        tello.command('back 20')
                    elif e.button == buttons.CIRCLE:
                        tello.command('right 20')
                    elif e.button == buttons.SQUARE:
                        tello.command('left 20')
                elif e.type == pygame.locals.JOYBUTTONUP:
                    tello.disableRepeat()
        except KeyboardInterrupt, e:
            print (e)
            tello.command('quit')
            exit(1)

if __name__ == '__main__': main()

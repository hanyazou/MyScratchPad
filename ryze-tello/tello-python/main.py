#!/usr/bin/python

#
# RYZE Tello toy drone SDK and PS3 joystick
#

import time
import sys
import tello
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

def main():
    pygame.init()
    pygame.joystick.init()
    try:
        js = pygame.joystick.Joystick(0)
        js.init()
        print 'Joystick name: ' + js.get_name()
    except pygame.error:
        print 'no joystick found'

    drone = tello.Tello()

    while 1:
        try:
            time.sleep(0.01)  # loop with pygame.event.get() is too mush tight w/o some sleep
            for e in pygame.event.get():
                if e.type == pygame.locals.JOYAXISMOTION: # 7
                    x , y = js.get_axis(0), js.get_axis(1)
                    # print 'x and y : ' + str(x) +' , '+ str(y)
                elif e.type == pygame.locals.JOYBUTTONDOWN: # 10
                    if e.button == buttons.L2:
                        drone.command('takeoff')
                    elif e.button == buttons.L1:
                        drone.command('land')
                    elif e.button == buttons.UP:
                        drone.command('up 20')
                    elif e.button == buttons.DOWN:
                        drone.command('down 20')
                    elif e.button == buttons.RIGHT:
                        drone.command('cw 20')
                    elif e.button == buttons.LEFT:
                        drone.command('ccw 20')
                    elif e.button == buttons.TRIANGLE:
                        drone.command('forward 20')
                    elif e.button == buttons.CROSS:
                        drone.command('back 20')
                    elif e.button == buttons.CIRCLE:
                        drone.command('right 20')
                    elif e.button == buttons.SQUARE:
                        drone.command('left 20')
                elif e.type == pygame.locals.JOYBUTTONUP:
                    drone.disableRepeat()
        except KeyboardInterrupt, e:
            print (e)
            drone.command('quit')
            exit(1)

if __name__ == '__main__': main()

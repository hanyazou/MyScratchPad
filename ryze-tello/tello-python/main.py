#!/usr/bin/python

#
# RYZE Tello toy drone SDK and PS4 joystick
#

import time
import sys
import tello
import pygame
from pygame.locals import *


class ButtonsPS3:
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


class ButtonsPS4:
    UP = -1
    RIGHT = -1
    DOWN = -1
    LEFT = -1
    L2 = 6
    R2 = 7
    L1 = 4
    R1 = 5
    TRIANGLE = 3
    CIRCLE = 2
    CROSS = 1
    SQUARE = 0


def main():
    pygame.init()
    pygame.joystick.init()
    try:
        js = pygame.joystick.Joystick(0)
        js.init()
        print 'Joystick name: ' + js.get_name()

    except pygame.error:
        print 'no joystick found'

    buttons = ButtonsPS4
    drone = tello.Drone()
    drone.connect()
    speed = 30

    try:
        while 1:
            time.sleep(0.01)  # loop with pygame.event.get() is too mush tight w/o some sleep
            for e in pygame.event.get():
                if e.type == pygame.locals.JOYAXISMOTION:
                    x, y = js.get_axis(0), js.get_axis(1)
                    # print 'x and y : ' + str(x) +' , '+ str(y)
                elif e.type == pygame.locals.JOYHATMOTION:
                    if e.value[0] < 0:
                        drone.counter_clockwise(speed)
                    if e.value[0] == 0:
                        drone.clockwise(0)
                    if e.value[0] > 0:
                        drone.clockwise(speed)
                    if e.value[1] < 0:
                        drone.down(speed)
                    if e.value[1] == 0:
                        drone.up(0)
                    if e.value[1] > 0:
                        drone.up(speed)
                elif e.type == pygame.locals.JOYBUTTONDOWN:
                    if e.button == buttons.L1:
                        drone.land()
                    elif e.button == buttons.UP:
                        drone.up(speed)
                    elif e.button == buttons.DOWN:
                        drone.down(speed)
                    elif e.button == buttons.RIGHT:
                        drone.clockwise(speed)
                    elif e.button == buttons.LEFT:
                        drone.counter_clockwise(speed)
                    elif e.button == buttons.TRIANGLE:
                        drone.forward(speed)
                    elif e.button == buttons.CROSS:
                        drone.backward(speed)
                    elif e.button == buttons.CIRCLE:
                        drone.right(speed)
                    elif e.button == buttons.SQUARE:
                        drone.left(speed)
                elif e.type == pygame.locals.JOYBUTTONUP:
                    if e.button == buttons.L2:
                        drone.takeoff()
                    elif e.button == buttons.UP:
                        drone.up(0)
                    elif e.button == buttons.DOWN:
                        drone.down(0)
                    elif e.button == buttons.RIGHT:
                        drone.clockwise(0)
                    elif e.button == buttons.LEFT:
                        drone.counter_clockwise(0)
                    elif e.button == buttons.TRIANGLE:
                        drone.forward(0)
                    elif e.button == buttons.CROSS:
                        drone.backward(0)
                    elif e.button == buttons.CIRCLE:
                        drone.right(0)
                    elif e.button == buttons.SQUARE:
                        drone.left(0)
    except KeyboardInterrupt, e:
        print (e)
    except Exception, e:
        print (e)

    drone.quit()
    exit(1)

if __name__ == '__main__':
    main()

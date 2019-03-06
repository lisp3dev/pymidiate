# -*- coding: utf-8 -*-

from midiate.zoom.g1on import *
from midiate import *
import pygame

pygame.init()
pygame.joystick.init()
try:
    js = pygame.joystick.Joystick(0)
    js.init()
except pygame.error:
    raise Exception('Joystick not found')

mid = Midiator()
mid.start_process()

g1 = G1on(midiator=mid)
g1.connect()

amp,chorus,delay,reverb,_ = g1.make_patch('MSDRIVE','Chorus','Delay','Arena')

amp['OUT'] = 'ComboFront'
delay['Tail'] = 'ON'

mode = None
def turn_mode_if_needed(m):
    global mode
    if m != mode:
        mode = m
        if mode == 1:
            chorus.off(); delay.off(); reverb.on()
            #amp['Gain','Level','Trebl'] = 50,120,60
            print('mode 1')
        elif mode == 2:
            chorus.on(); delay.on(); reverb.off()
            #amp['Gain','Level','Trebl'] = 100,100,50
            print('mode 2')

turn_mode_if_needed(1)
            
def operate(dev, msg, raw):
    note = raw[1]
    if note <= 52:
        turn_mode_if_needed(1)
    elif note >= 63:
        turn_mode_if_needed(2)

ctrl_in = mid.open_input(name='UM-1',translate=8)
mid.register_callback(ctrl_in, b'9', operate)
mid.listen(ctrl_in)

param = 100
def setparam():
    chorus['Depth'] = param//2
    amp['Gain'] = param
    print(f'パラメータ変更: amp.Gain = chorus.Depth = {param}')

while True:
    e = pygame.event.wait()
    if e.type==pygame.JOYBUTTONDOWN:
        btn = e.button
        if btn in (7,8): # press Select or Start to quit
            break
        elif btn==0: # button A
            if param > 10:
                param -= 10
                setparam()
        elif btn==1: # button B
            if param < 100:
                param += 10
                setparam()


g1.disconnect()
mid.stop_process()

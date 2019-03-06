# -*- coding: utf-8 -*-

from midiate.zoom.g1on import *
from midiate import *

mid = Midiator()
mid.start_process()

g1 = G1on(midiator=mid)
g1.connect()

znr,stomp,amp,chorus,delay = g1.make_patch('ZNR','TScream','MS1959','Chorus','StompDly')

amp['OUT']='ComboFront'
delay['Tail'] = 'ON'
stomp['Gain'] = 70

mode = None
def turn_mode_if_needed(m):
    global mode
    if m != mode:
        mode = m
        if mode == 1:
            znr.off(); stomp.off(); chorus.off(); delay.off()
            amp['Gain','Level','Trebl'] = 100,120,60
            print('mode 1')
        elif mode == 2:
            znr.on(); stomp.on(); chorus.on(); delay.on()
            amp['Gain','Level','Trebl'] = 50,100,50
            print('mode 2')

turn_mode_if_needed(1)
            
def operate(dev, msg, raw):
    note = raw[1]
    if note <= 52:
        turn_mode_if_needed(1)
    elif note >= 63:
        turn_mode_if_needed(2)

#ctrl_in = mid.open_input(candidates=('UM-1','loopMIDI Port'),translate=8)
#ctrl_in = mid.open_input(name='loopMIDI Port',translate=8)
ctrl_in = mid.open_input(name='UM-1',translate=8)
mid.callback(ctrl_in, b'9', operate)
mid.listen(ctrl_in)

input('press any key to quit')

g1.disconnect()
mid.stop_process()

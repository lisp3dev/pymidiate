# -*- coding: utf-8 -*-

from midiate.zoom.g1on import *
from midiate import *

mid = Midiator()
mid.start_process()

g1 = G1on(midiator=mid)
g1.connect()

amp,chorus,delay,reverb,_ = g1.make_patch('MSDRIVE','Chorus','Delay','Arena')

amp['OUT'] = 'ComboFront'
delay['Tail'] = 'ON'
#stomp['Gain'] = 70

mode = None
def turn_mode_if_needed(m):
    global mode
    if m != mode:
        mode = m
        if mode == 1:
            chorus.off(); delay.off(); reverb.on()
            amp['Gain','Level','Trebl'] = 50,120,60
            print('mode 1')
        elif mode == 2:
            chorus.on(); delay.on(); reverb.off()
            amp['Gain','Level','Trebl'] = 100,100,50
            print('mode 2')

turn_mode_if_needed(1)
            
def operate(dev, msg, raw):
    note = raw[1]
    if note <= 52:
        turn_mode_if_needed(1)
    elif note >= 63:
        turn_mode_if_needed(2)
    print(note)

#ctrl_in = mid.open_input(candidates=('UM-1','loopMIDI Port'),translate=8)
#ctrl_in = mid.open_input(name='loopMIDI Port',translate=8)
ctrl_in = mid.open_input(name='UM-1',translate=8)
mid.callback(ctrl_in, b'9', operate)
mid.listen(ctrl_in)

input('press any key to quit')

g1.disconnect()
mid.stop_process()

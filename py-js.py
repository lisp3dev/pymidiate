# -*- coding: utf-8 -*-
# ジョイスティックを楽器にする

import midiate
import pygame as pgm

pgm.init()
pgm.joystick.init()
try:
    js = pgm.joystick.Joystick(0)
    js.init()
except pgm.error:
    raise Exception('Joystick not found')


mid = midiate.Midiator()
mid.start_process()
#outdev= mid.open_output(name='Microsoft GS Wavetable Synth')
outdev= mid.open_output(name='CASIO USB-MIDI')
mid.send(outdev, 'C010')

JS_STOP  = 7  #終了ボタン

JS_REPEAT = 0

JS_T = 3
JS_D = 2 
JS_2 = 1

JS_SD = 1
JS_3 = 3
JS_6 = 0 
JS_7 = 2 

JS_SHIFT = 6
JS_ADD7 = 4
JS_ADD9 = 5


MAJOR = (0,2,4,5,7,9,11)
MINOR = (0,2,3,5,7,8,10)
TABLE = (JS_T, JS_2, None, None, JS_D)
TABLE2 = (None,None,JS_3,JS_SD,None,JS_6,JS_7)

def make_scale(xs):
    scale = []
    for octave in range(0,10):
        base = octave*12
        for x in xs:
            scale.append(base+x)
    return scale

scale = make_scale(MAJOR)
#scale = make_scale(MINOR)

current_notes = []
current_base_index = 7*4
current_root_index = None
add_7_needed = False
add_9_needed = False
shift = False

def mkmsg(cmd,ch,x,y):
    return b'%d%X%02X%02X'%(cmd,ch,x,y)

def noteoff_if_needed():
    global current_notes
    if current_notes:
        for note in current_notes:
            mid.send(outdev,mkmsg(8,0,note,0))

def detect(notes):
    root_name = ('C','C#','D','D#','E','F','F#','G','G#','A','A#','B')[notes[0]%12]
    tone = '' if notes[1]-notes[0] == 4 else 'm'
    added = ''
    if len(notes) == 5:
        added = ' +7th,9th'
    if len(notes) == 4:
        m = notes[3] - notes[0];
        if m < 12: added = ' +7th'
        else: added = ' +9th'
        
    return root_name + tone + added

def exec_chord(notes):
    for note in notes:
        mid.send(outdev, mkmsg(9,0,note,127))
    print('   ',detect(notes))

def noteon(index):
    noteoff_if_needed()
    global current_root_index
    current_root_index = index
    root = scale[index]
    third = scale[index+2]
    fifth = scale[index+4]
    global current_notes
    current_notes = [root,third,fifth]
    if add_7_needed: current_notes.append(scale[index+6])
    if add_9_needed: current_notes.append(scale[index+8])
    exec_chord(current_notes)
                 
def repeat():
    noteoff_if_needed()
    if current_notes:
        exec_chord(current_notes)
                 
while True:
    e = pgm.event.wait()
    if e.type==pgm.JOYBUTTONDOWN: #and e.button==JS_QUITBTN:
        btn = e.button
        if btn==JS_STOP:
            if current_notes:
                noteoff_if_needed()
                current_notes = None
            else: break
        elif not shift and btn in TABLE:
            index = TABLE.index(btn)
            noteon(current_base_index + index)
        elif shift and btn in TABLE2:
            index = TABLE2.index(btn)
            noteon(current_base_index + index)
        elif btn == JS_REPEAT: repeat()
        elif btn == JS_ADD7: add_7_needed = True
        elif btn == JS_ADD9: add_9_needed = True
        elif btn == JS_SHIFT: shift = True
    
        
    elif e.type==pgm.JOYBUTTONUP:
        btn = e.button
        if btn == JS_ADD7: add_7_needed = False
        elif btn == JS_ADD9: add_9_needed = False
        elif btn == JS_SHIFT: shift = False

    elif e.type==pgm.JOYAXISMOTION and e.axis==0 and current_root_index:
        if e.value > 0.5: 
            noteon(current_root_index + 3)
        elif e.value < -0.5: 
            noteon(current_root_index - 4)

    
    elif e.type==pgm.JOYAXISMOTION and e.axis==1:
        if e.value > 0.5 and current_base_index > 1: 
            current_base_index -= 7
            if current_root_index: current_root_index -= 7
        elif e.value < -0.5 and current_base_index < 50: 
            current_base_index += 7
            if current_root_index: current_root_index += 7




mid.stop_process()

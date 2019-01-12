# -*- coding: utf-8 -*-
import midiate
import devel

midiate = midiate.Midiate()
midiate.start_process()
indev = devel.open_input(midiate);


def get_note_name(midi_note):
    mod = midi_note % 12
    return ('C','C#','D','D#','E','F','F#','G','G#','A','A#','B')[mod]


def mon(dev, sig , raw):
    sig_type = ''
    chk = raw[0]&0xF0
    if   chk==0x90: sig_type = 'NOTE ON - ' + get_note_name(raw[1])
    elif chk==0x80: sig_type = 'NOTE OFF - ' + get_note_name(raw[1])
    elif chk==0xB0: sig_type = 'CONTROL CHANGE'
    elif chk==0xC0: sig_type = 'PROGRAM CHANGE'
    devel.status(f'{sig.decode()} {sig_type}')
    print('受信: ', dev, sig, raw)
    
midiate.callback(indev,'******',mon)
midiate.listen(indev);


devel.wait(title='MIDI signal monitor', text='信号をモニタするよDEMO')

midiate.stop_process()

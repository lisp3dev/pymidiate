# -*- coding: utf-8 -*-
import midiate
import devel

mid = midiate.Midiator()
mid.start_process()
#indev = devel.open_input(mid);
indev = mid.open_input(name='ZOOM 1 Series')


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
    
mid.callback(indev,'******',mon)
mid.listen(indev);


devel.wait(title='MIDI signal monitor', text='信号をモニタするよDEMO')

mid.stop_process()

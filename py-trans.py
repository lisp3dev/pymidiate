# -*- coding: utf-8 -*-
import midiate
import devel

mid = midiate.Midiator();
mid.start_process()
indev,outdev = devel.open_both_io(mid)
for i in range(6):
    mid.send(outdev, 'C%X00'%i)
    mid.send(outdev, 'B%X7B00'%i)
    
#mid.send(outdev, 'B07A00')
#mid.send(outdev, 'B07800')

origin = 0

CMDKEY_MIN, CMDKEY_MAX = 24,35
CHORDKEY_MIN, CHORDKEY_MAX = 36,47

pending_keys = []
pending_origin = None

SCALE_MAJ = (2,2,1,2,2,2,1)
NOTES_MAJ = (0,2,4,5,7,9,11)

def chord_intervals(mode):
    print('MODE', mode)
    result,interval = [],0
    for i in range(6):
        interval += SCALE_MAJ[(i+mode)%7]
        if i%2:
            result.append(interval)

    return result

def recv(dev, msg, raw):
    global origin, pending_origin
    st = raw[0]
    ch = raw[0]&0xF
    cmd = (raw[0]&0xF0)>>4
    note = raw[1]
    vel = raw[2]
    print(msg)
    #print(cmd, ch, origin+note, vel)
    if cmd in (0x9,0x8):
        if note >= CMDKEY_MIN and note <= CMDKEY_MAX:
            if cmd==0x9 and vel>0:
                pending_origin = note%12
                if not pending_keys:
                    origin,pending_origin = pending_origin, None
                print('transpose!',origin)
        else:
            mid.send(outdev, b'%d%X%02X%02X'%(cmd,0, origin+note, vel))
            if note >= CHORDKEY_MIN and note <= CHORDKEY_MAX:
                pos = note%12
                if pos in NOTES_MAJ:
                    mode = NOTES_MAJ.index(pos)
                    for (i,interval) in enumerate(chord_intervals(mode)):
                        print('CHORD',origin,note,interval)
                        mid.send(outdev, b'%d%X%02X%02X'%(cmd,1+i, origin+note+interval+12, vel))
                mid.send(outdev, b'%d%X%02X%02X'%(cmd,4, origin+note+12, vel))
                mid.send(outdev, b'%d%X%02X%02X'%(cmd,4, origin+note-12, vel))
                    
            if cmd==0x9 and vel>0:
                pending_keys.append(note)
            else:
                pending_keys.remove(note)
                if not pending_keys and pending_origin:
                    origin,pending_origin = pending_origin, None
                    
            print(pending_keys)
    print(f'Note = {note}')
                 
mid.callback(None,'******', recv)
mid.listen(indev);

devel.wait(title='transposer',
           text='トランスポーズ')

mid.stop_process()

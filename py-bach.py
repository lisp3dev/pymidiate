# -*- coding: utf-8 -*-

import time
import midiate
import devel
import studuino
led = None

mid = midiate.Midiator()
mid.start_process()
indev,outdev = devel.open_both_io(mid);
mid.send(outdev, b'C%X%02X'%(indev,34))

current_base_note = None
current_note = None
song = [0,2,4,7,5,5,9,7,7,12,11,12,7,4,0,2,4,5,7,9,7,5,4,2,4,0, -1,0,2,-5,-1,2,5,4,2,4,
        0,2,4,7,5,5,9,7,7,12,11,12,7,4,0,2,4, 2,7,5,4,2,0,-5,0,-1,0,4,7,12,7,4,0,4, 6,
        7,-5,-3,-1,2,1,1,4,2,2,5,4,5,2,-3,-7,-5,-3,-2,7,5,7,4,1,-3,-1,1,
        2,5,4,5,9,7,7,10,9,9,14,13,14,9,5,2,4,5, 10,9,7,5,4,2,-3,2,1,2,5,9,14,9,5,2 ]
        
song_pos = 0
def get_song_note():
    global current_note, song_pos
    current_note = song[song_pos] + current_base_note
    song_pos += 1
    if song_pos >= len(song): song_pos = 0
    return current_note

def bach(dev, msg, raw):
    global led
    global current_base_note, current_note, song_pos
    if raw[0]&0xF0 == 0x90 and raw[2]>0:
        ch = raw[0]&0xF
        note = raw[1]
        vel  = raw[2]
        if current_base_note and note != current_base_note and note%12 == current_base_note%12:
            mid.send(outdev,b'9%X%02X%02X'%(ch,current_note,vel))
            return
        elif note != current_base_note:
            mid.send(outdev, b'B%X7B00'%ch)
            current_base_note = note
            song_pos = 0
        song_note = get_song_note()
        mid.send(outdev,b'9%X%02X%02X'%(ch,song_note,vel))
        led.on()
    elif raw[0]&0xF0 == 0x80 or (raw[0]&0xF0 == 0x90 and raw[2]==0):
        ch = raw[0]&0xF
        note = raw[1]
        if note == current_base_note or note%12 == current_base_note%12:
            mid.send(outdev,b'8%X%02X00'%(ch,current_note))
            led.off()
        else:
            mid.send(outdev,msg)
    print('受信: ', dev, msg)


mid.callback(None,'******', bach)
#mid.send(outdev, 'C030')
mid.listen(indev);

studuino.start('COM3')
time.sleep(2)
led = studuino.LED()
led.attach(studuino.A0)

devel.wait(title="let's sing!",
           text='バッハの「主よ人の望みの喜びよ」を歌うよ！\n'
           '最初に叩いたキーのノートが調のトニックになるよ\n'
           'オクターブ関係のキーを叩くと直前のノートを繰り返せるよ')

mid.stop_process()
studuino.stop()

# -*- coding: utf-8 -*-
import midiate
import devel
from random import randint
from time import sleep

mid = midiate.Midiator();
mid.start_process()
indev,outdev = devel.open_both_io(mid)
for i in range(2):
    mid.send(outdev, 'C%X00'%i)
    mid.send(outdev, 'B%X7B00'%i)

#mid.send(outdev, 'B07A00')
#mid.send(outdev, 'B07800')

def generate_target_note(guide):
    while True:
        target = guide + randint(-7,7)
        if target != guide and target >= 0 and target <= 127:
            return target

guide_note = None
target_note = None

def perform_target_note():
    mid.send(outdev, b'90%02X7F'%target_note)
    sleep(1.0)
    mid.send(outdev, b'80%02X00'%target_note)

def perform_pingpong():
    # ピンポン音
    ping = 100
    pong = ping-4
    mid.send(outdev, b'91%02X7F'%ping)
    sleep(0.2)
    mid.send(outdev, b'91%02X7F'%pong)
    sleep(1.0)
    mid.send(outdev, b'81%02X00'%ping)
    mid.send(outdev, b'81%02X00'%pong)

def correct():
    global guide_note, target_note
    guide_note = None
    perform_pingpong()
    
def wrong():
    pass

def recv_on(dev, msg, raw):
    print('on', msg)
    note = raw[1]

    if guide_note is None or guide_note == note:
        mid.send(outdev, b'90%02X7F'%note)
    elif target_note:
        if target_note == note:
            mid.send(outdev, b'90%02X7F'%note)
            correct()
        else:
            wrong()

def recv_off(dev, msg, raw):
    print('off', msg)
    global guide_note, target_note

    note = raw[1]

    if target_note == note:
        target_note = None
        mid.send(outdev, b'80%02X00'%note)
    elif guide_note is None or guide_note  == note:
        mid.send(outdev, b'80%02X00'%note)
        if guide_note is None:
            guide_note = note
            target_note = generate_target_note(guide_note)
        perform_target_note()
                 
mid.callback(None,'8*****', recv_off)
mid.callback(None,'9*****', recv_on)
mid.listen(indev);

devel.wait(title='sol1',
           text='相対音感トレーニング')

mid.stop_process()

# -*- coding: utf-8 -*-

import midiate
import devel
import random

midiate.start_process()
indev,outdev = devel.open_both_io();

count_success, count_failed = 0,0

def thru(dev, msg, raw):
    global count_success, count_failed
    if raw[0]&0xF0 in {0x90,0x80}:
        if raw[1]%12 in {1,3,4,6,8,10,11}:
            midiate.send(outdev, msg)
            if raw[0]&0xF0 == 0x90 and raw[2]>0:
                count_success += 1
                devel.status(f'{count_success+count_failed}回中、ミスタッチ{count_failed}回')
        else:
            if raw[0]&0xF0 == 0x90 and raw[2]>0:
                count_failed += 1
                prog = random.randint(0,47)
                devel.status(f'間違えんなドアホっ！\nお仕置きじゃ！\n音色を{prog}番に変えたったぞ！')
                midiate.send(outdev, b'C%X%02X'%(raw[0]&0xF,prog))

    else: midiate.send(outdev, msg)
    print('受信: ', dev, msg)
    
midiate.callback(None,'******', thru)
midiate.listen(indev);

devel.wait(title='signal masking',
           text='信号の取捨選択 Bメジャーのスケールノートだけ通すよ！\n'
           '間違えるたびにランダムに音色が変わるよ')

midiate.stop_process()

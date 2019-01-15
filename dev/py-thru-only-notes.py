# -*- coding: utf-8 -*-

import midiate
import devel

mid = midiate.Midiator()
mid.start_process()
indev,outdev = devel.open_both_io(mid);
mid.send(outdev, 'C010')

count = 0
def thru(dev, msg, raw):
    global count
    mid.send(outdev, msg)
    count += 1
    devel.status(f'{count}個の信号を中継したよ！')
    print('受信: ', dev, msg, raw)
    
mid.callback(indev,'9,8', thru)
mid.listen(indev);

devel.wait(title='signal thru',text='単純な信号の中継(ノート信号のみ)')

mid.stop_process()

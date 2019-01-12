# -*- coding: utf-8 -*-

import midiate
import devel

midiate.start_process()
indev,outdev = devel.open_both_io();
midiate.send(outdev, 'C000')

count = 0
def thru(dev, msg, raw):
    global count
    midiate.send(outdev, msg)
    count += 1
    devel.status(f'{count}個の信号を中継したよ！')
    print('受信: ', dev, msg, raw)
    
midiate.callback(None,'******', thru)
midiate.listen(indev);

devel.wait(title='signal thru',text='単純な信号の中継')

midiate.stop_process()

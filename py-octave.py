# -*- coding: utf-8 -*-
import midiate
import devel

mid = midiate.Midiator()
mid.start_process()
indev,outdev = devel.open_both_io(mid);

not_initialized = True
def init(cur_ch,ch1,ch2):
    global not_initialized
    not_initialized = False
    mid.send(outdev, b'C%X%02X'%(cur_ch,0))
    mid.send(outdev, b'C%X%02X'%(ch1,34))
    mid.send(outdev, b'C%X%02X'%(ch2,0))

def op(dev, msg, raw):
    cmd = (raw[0]&0xF0)>>4
    note = raw[1]
    vel = raw[2]
    if vel>0: vel = 127 # ベロシティ固定
    cur_ch = raw[0]&0xF    
    ch1 = (cur_ch + 1)%16  # 別のチャンネル
    ch2 = (cur_ch + 2)%16  # さらに別のチャンネル
    if not_initialized: init(cur_ch,ch1,ch2)
    mid.send(outdev, msg)
    mid.send(outdev, b'%d%X%02X%02X'%(cmd,ch1,note-24,vel))
    mid.send(outdev, b'%d%X%02X%02X'%(cmd,ch2,note+12,vel))
    print('受信: ', dev, msg)


def thru(dev,msg,raw):
    mid.send(outdev, msg)
    print('受信(OTHER): ', dev, msg)

mid.callback(None,'9,8', op)
mid.callback(None,'otherwise', thru)
mid.listen(indev);

devel.wait(title='simple octaver',
           text='オクターバー！\n'
           '２オクターブ下をベースの音色で、\n'
           '１オクターブ上をピアノの音色で同時に鳴らすよ\n'
           'ベロシティは最大音量に固定するよ')

mid.stop_process()

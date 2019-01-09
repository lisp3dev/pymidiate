# -*- coding: utf-8 -*-

import midiate
import devel

midiate.start_process()
indev,outdev = devel.open_both_io();

current_notes = set([]) #現在なっている音の集合

def sustainer(dev, msg, raw):
    global current_notes
    if raw[0]&0xF0 == 0x90 and raw[2]>0:
        note = raw[1]
        if note in current_notes:
            midiate.send(outdev, b'8%X%02X00'%(raw[0]&0xF,note))
            current_notes.remove(note)
        else:
            midiate.send(outdev, msg)
            current_notes.add(note)
        devel.status(f'現在の同時発音数 = {len(current_notes)}')
    print('受信: ', dev, msg)


def make_all_notes_off(dev, msg, raw):
    # 強制的に全チャンネルの発音を停止させる
    for ch in range(16):
        midiate.send(outdev, b'B%X7B00'%ch)
    global current_notes
    devel.status('コントロールチェンジ信号受信\n音源にオールサウンドオフ信号を送ったよ！')
    current_notes = set([])

## TODO: callbackの同一ターゲットデバイスに複数コールバックを設定すると不具合が起きる問題を修正せよ
## 下記のようにすれば通る
## この問題は修正済み
midiate.callback(indev,'9', sustainer)
midiate.callback(indev,'B', make_all_notes_off)
midiate.send(outdev, 'C030')
midiate.listen(indev);

devel.wait(title='sustainer',
           text='発音状態を継続させるよ！\n'
           'もう一度同じキーを叩くとノートオフ信号を送るよ\n'
           'コントロールチェンジ信号を受信すると全ての音を止めるよ')

midiate.stop_process()

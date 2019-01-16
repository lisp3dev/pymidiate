# -*- coding: utf-8 -*-

import studuino
import time
import midiate
import devel

studuino.start('COM4')
time.sleep(1)
leds = [studuino.LED(), studuino.LED()]
leds[0].attach(studuino.A0)
leds[1].attach(studuino.A1)
buzzer = studuino.Buzzer()
buzzer.attach(studuino.A4)

mid = midiate.Midiator()
mid.start_process()
indev = devel.open_input(mid);

count = 0

def st_bz_on(note):
    buzzer.on(note % 12, note // 12)
    print('BUZZER: ',note)
def st_bz_off():
    buzzer.off()
    print('BUZZER OFF')

def st_led_on():
    leds[count%2].on()
    print('LED on')
def st_led_off():
    leds[count%2].off()
    print('LED off')

def on(dev, msg, raw):
    if raw[2] == 0:
        return off(dev,msg,raw)
    global count
    count += 1
    st_bz_on(raw[1])
    devel.status(f'{count}個の発音信号をスタディーノに送ったよ！')
    st_led_on()
    print('受信: ', dev, msg, raw)

def off(dev, msg, raw):
    st_bz_off()
    st_led_off()
    
mid.callback(indev,'9', on)
mid.callback(indev,'8', off)
mid.listen(indev);


devel.wait(title='studuino buzzer test',text='studuinoのブザーを鳴らすよ')

studuino.stop()

mid.stop_process()

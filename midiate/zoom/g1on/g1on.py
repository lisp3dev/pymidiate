# -*- coding: utf-8 -*-
#  This file is part of pymidiate.

#############################################################
##             pymidiate / midiate.zoom.g1on               ##
## Copyright (C) 2019 PGkids Laboratory <lab@pgkids.co.jp> ##
#############################################################


import midiate
import threading
from .core import init5,p1,p2,p3,p4,p5,fxinfos,fxids,G1onFx

def _encode_patch_name(name):
    bytes = name.encode()
    n = len(bytes)
    if n>10:
        raise(ValueError)
    if n<10:
        bytes = bytes + b' ' * (10-n)
    result = b''
    for c in bytes[0:4]: result += b'%02X' % c
    result += b'00'
    for c in bytes[4:]:  result += b'%02X' % c
    result += b'00'

    return result

def _encode_patch_level(level):
    if not isinstance(level,int):
        raise(ValueError)
    if level < 0 or level > 120:
        raise(ValueError)
    return b'%02X' % level

def _join_b3_and_b4(fx3, b3, fx4, b4):
    if fx3 is 'BYPASS': fx3 = None
    if fx4 is 'BYPASS': fx4 = None

    if (not fx3 and not fx4) or not fx4:
        return b3+b4[3:]
    elif not fx3:
        return b3[:-3]+b4
    # 第３チェインと第４チェインの重複区間のチェック
    # ほとんど内部解析していないので現時点ではとりあえず続行
    elif b3[-3:] != b4[0:3]:
        #return b3+b4[3:]
        return b3[:-3]+b4
        #raise(ValueError)
    else:
        return b3+b4[3:]

def _mkpatch(fx1=None, fx2=None, fx3=None, fx4=None, fx5=None, 
            level=100, name='midiator'):
    idxs = []
    for id in (fx1,fx2,fx3,fx4,fx5):
        if id is None: id = 'BYPASS'
        if not id in fxids:
            raise(ValueError)
        idxs.append(fxids.index(id))
    b1,b2,b3,b4,b5 = p1[idxs[0]],p2[idxs[1]],p3[idxs[2]],p4[idxs[3]],p5[idxs[4]]
    joined_b3b4 = _join_b3_and_b4(fx3,b3,fx4,b4)

    msg = init5[0:10]+b1+b2+init5[84:90]+joined_b3b4+init5[166:170]+b5+init5[208:220]+_encode_patch_level(level)+init5[222:242]+_encode_patch_name(name)+b'F7'

    return msg
        
class G1on():
    __odev = None
    __idev = None
    __own_midiator = None
    def __init__(self, receiver=None, *, midiator=None):
        if midiator:
            # midiatorを外部から借りる場合
            self.__midi = midiator
        else:
            # midiatorを自前で用意 (デフォルト)
            self.__midi = midiate.Midiator(monitor_stderr=False)
            self.__own_midiator = self.__midi

        self.__receiver = receiver

    def connect(self):
        mid = self.__midi
        if self.__own_midiator:
            mid.start_process()
            #mid.debug(True)
        self.__odev = mid.open_output(name='ZOOM 1 Series')
        if not self.__odev:
            raise(Exception('could not open G1on MIDI output port'))
        if self.__receiver:
            self.__idev = mid.open_input(name='ZOOM 1 Series')
        if not self.__odev:
            raise(Exception('could not open G1on MIDI input port'))
            mid.callback(self.__idev, b'*', self.__receiver)
            mid.listen(self.__idev)

        mid.send(self.__odev, b'F052006350F7')
        
    def disconnect(self):
        self.__midi.send(self.__odev, b'F052006351F7')
        #self.__midi.close(self.__odev) #todo
        if self.__idev:
            #self.__midi.close(self.__idev) #todo
            pass
        if self.__own_midiator:
            self.__midi.sync()
            self.__midi.stop_process()

        self.__midi = self.__own_midiator = self.__idev = self.__odev = None
        
    def clear_patch(self):
        self.__midi.send(self.__odev, init5)

    def make_patch(self,
                   fx1=None, fx2=None, fx3=None, fx4=None, fx5=None, *,
                   st1=True, st2=True, st3=True, st4=True, st5=True, 
                   level=100, name='pyMidiate'):
        msg = _mkpatch(fx1, fx2, fx3, fx4, fx5, level, name)
        self.__midi.send(self.__odev, msg)
        if not st1: self.__set_fx_state(0,0)
        if not st2: self.__set_fx_state(1,0)
        if not st3: self.__set_fx_state(2,0)
        if not st4: self.__set_fx_state(3,0)
        if not st5: self.__set_fx_state(4,0)
        return self.make_controllers(fx1,fx2,fx3,fx4,fx5)

    def make_controllers(self, fx1=None, fx2=None, fx3=None, fx4=None, fx5=None):
        controllers = []
        for (fx_index,id) in enumerate((fx1,fx2,fx3,fx4,fx5)):
            if id is None: id = 'BYPASS'
            rules = fxinfos[id]
            controllers.append( G1onFx(self, fx_index, id, rules) )

        return tuple(controllers)
        
            
    def __set_fx_state(self, index, bit):
        msg = b'F052006331%02X00%02X00F7' % (index, bit)
        self.__midi.send(self.__odev, msg)

    def set_fx_state(self, fx_pos, st:bool):
        if not isinstance(fx_pos,int) or fx_pos<1 or fx_pos>5:
            raise(ValueError)
        self.__set_fx_state(fx_pos-1, 1 if st else 0)

    # _set_fx_param(i,0,bit) と __set_fx_state(i,bit) は等価である
    # _set_fx_param(i,1,x) (xは1以上)とすると、どうやら全パラメータがリセットされるらしい
    # ただし、xを前回と同じ値にすると何故かリセットされない
    def _unsafe_set_fx_param(self, fx_index, param_index, value, value2=0):
        if value>0x7F:
            value2 = value // 0x7F
            value  %= 0x7F
        msg = b'F052006331%02X%02X%02X%02XF7' % (fx_index, param_index, value, value2)
        self.__midi.send(self.__odev, msg)
                       
    def set_fx_param(self, fx_pos, param_pos, value):
        if fx_pos<1 or fx_pos>5 or param_pos<1 or param_pos>30 or not isinstance(value,int) or value<0:
            raise(ValueError)
        self._unsafe_set_fx_param(fx_pos-1, param_pos+1, value)
        
    def send_to_g1on(self, midi_msg):
        self.__midi.send(self.__odev, midi_msg)

    # Bank = 'A'-'J' or ('a'-'j')  Num=1..10
    def select_patch(self, bank_name, patch_number):
        if 'A' <= bank_name <= 'J':
            segment = ord(bank_name) - ord('A')
        elif 'a' <= bank_name <= 'j':
            segment = ord(bank_name) - ord('a')
        else:
            raise(Exception(f"'{bank}' is not valid Bank name"))
        if 0 <= patch_number <= 9:
            internal_patch_index = segment*10 + patch_number
            self.send_to_g1on(b'C0%02X'%internal_patch_index)
            


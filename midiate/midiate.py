# -*- coding: utf-8 -*-

##################################################################
##                         pymidiate                            ##
## Copyright (C) 2018-2019 PGkids Laboratory <lab@pgkids.co.jp> ##
##################################################################


import sys
import subprocess
import threading
import time
import pkg_resources

def get_default_bin_path():
    path = pkg_resources.resource_filename(__name__, 'win32/intermidiator.exe')
    if path.lower().find('a:\\dropbox\\home\\git\\pymidiate\\')==0:
        # PGkids Laboratory Internal Environment
        print('---------- DEVELOP ----------')
        return 'a:/Dropbox/home/git/interMidiator/intermidiator.exe'
    else:
        # Public Environment
        return path

def chr2hex(ascii):
    if ascii <= 57: return (ascii-48)
    else:           return ascii-65 + 10

def int_from_hex3(c1,c2,c3):
    return (chr2hex(c1)*16+chr2hex(c2))*16+chr2hex(c3)

def int_from_hex2(c1,c2):
    return chr2hex(c1)*16+chr2hex(c2)

def take_handle_from_recv_msg(line):
    return int_from_hex3(line[2],line[3],line[4])


def decode_callback_id(line, i):
    result = 0
    ascii = line[i]
    while ascii>=48 and ascii<=57: # '0' to '9'
        result = result*10 + (ascii-48)
        i += 1
        ascii = line[i]
    return result

def decode_to_raw(b):
    length = len(b)
    if length <= 6:
        r1 = int_from_hex2(b[0],b[1])
        if length == 2: return (r1,)
        else:
            r2 = int_from_hex2(b[2],b[3])
            if length == 4: return (r1, r2)
            else: return (r1, r2, int_from_hex2(b[4],b[5]))
    else:
        # SysEx Message
        i, tmp = 0, []
        while i<length:
            tmp.append(int_from_hex2(b[i],b[i+1]))
            i += 2
        return tuple(tmp)
            

class MidiDevice():
    handle = None
class MidiInDevice(MidiDevice):
    def __init__(self, handle_in):
        self.handle = handle_in
class MidiOutDevice(MidiDevice):
    def __init__(self, handle_out):
        self.handle = handle_out
        
class Midiator():
    def __init__(self, *, monitor_stderr=False, interMidiator=get_default_bin_path()):
        self.interMidiator = interMidiator
        self.__proc = None
        self.__crlf = None
        self.endmsg = None
        self.__terminator = None
        self.__thread_monitor_stdout = None
        self.__thread_monitor_stderr = None
        self.__sem_1 = None
        self.__sem_2 = None
        self.__gResult = None
        self.__gError = None
        self.__callback_dic = None
        self.__prev_dev = None
        self.__prev_msg = None
        self.__prev_raw_msg = None
        self.__requires_monitor_stderr = monitor_stderr

    def __trunc(self,str):
        return str[0:(-2 if self.__crlf else -1)]

    def __monitor_stdout(self):
        while True:
            line = self.__proc.stdout.readline()
            if line==b'': return
            cmd = line[0];
            if cmd == ord('C'):
                id = decode_callback_id(line,2)
                #print('the id=',id)
                function = self.__callback_dic[id]
                if self.__prev_raw_msg is None: self.__prev_raw_msg = decode_to_raw(self.__prev_msg)
                function(self.__prev_dev, self.__prev_msg, self.__prev_raw_msg)
            elif cmd == ord('3'):
                self.__prev_dev = take_handle_from_recv_msg(line)
                self.__prev_msg = line[6:12]
                self.__prev_raw_msg = None
            elif cmd == ord('2'): 
                self.__prev_dev = take_handle_from_recv_msg(line)
                self.__prev_msg = line[6:10]
                self.__prev_raw_msg = None
            elif cmd == ord('1'):
                self.__prev_dev = take_handle_from_recv_msg(line)
                self.__prev_msg = line[6:8]
                self.__prev_raw_msg = None
            elif cmd == ord('X'):
                self.__prev_dev = take_handle_from_recv_msg(line)
                self.__prev_msg = line[6:(-2 if self.__crlf else -1)]
                self.__prev_raw_msg = None
            elif cmd == ord('{'):
                self.__gResult = []
                while True:
                    line = self.__proc.stdout.readline()
                    if line != (b'}\r\n' if self.__crlf else b'}\n'):
                        self.__gResult.append(self.__trunc(line).decode())
                    else: break
                self.__sem_1.release()
                self.__sem_2.acquire()
            elif cmd == ord('<'):
                self.__gResult = self.__trunc(line[2:])
                self.__sem_1.release()
                self.__sem_2.acquire()
            elif cmd == ord('!') or cmd == ord('F'):
                self.__gResult = None
                self.__gError = self.__trunc(line[2:])
                #sem_1.release()
                #sem_2.acquire()

            #else:        
            #print("[OUT]",line)
            sys.stdout.flush();

    def __monitor_stderr(self):
        while True:
            line = self.__proc.stderr.readline()
            if line==b'': return
            if self.__requires_monitor_stderr:
                print(line.decode(),end='')
                sys.stdout.flush();

    def _prepare(self):
        self.__proc = subprocess.Popen(self.interMidiator, #'a:/dropbox/home/git/intermidiator/intermidiator.exe',
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        s_ready = self.__proc.stdout.readline();
        if s_ready == b'READY\r\n' : self.__crlf, self.__terminator = True, b'\r\n'
        elif s_ready == b'READY\n' : self.__crlf, self.__terminator = False, b'\n'
        else:
            print('ERROR!')
            return False

        #__monitor_stdout, __monitor_stderr = self.generate_monitors();
        self.__thread_monitor_stdout = threading.Thread(target=self.__monitor_stdout)
        self.__thread_monitor_stderr = threading.Thread(target=self.__monitor_stderr)
        self.__sem_1 = threading.Semaphore(0)
        self.__sem_2 = threading.Semaphore(0)
        self.__callback_dic = {}
        return True

    def _start(self):
        self.__thread_monitor_stdout.start()
        self.__thread_monitor_stderr.start()

    def start_process(self):
        self._prepare()
        self._start()

    def debug(self, state:bool):
        self.__proc.stdin.write(b'DEBUG ')
        self.__proc.stdin.write(b'ON' if state else b'OFF')        
        self.__proc.stdin.write(self.__terminator)
    
    def __enum_io(self,cmd):
        self.__proc.stdin.write(cmd)
        self.__proc.stdin.write(self.__terminator)
        self.__proc.stdin.flush()
        self.__sem_1.acquire()
        names = self.__gResult;
        self.__sem_2.release()
        return names

    def enum_input(self):
        return self.__enum_io(b'LIST INPUT')
    def enum_output(self):
        return self.__enum_io(b'LIST OUTPUT')

    def __open_io(self, index, name, candidates, cmdHeader, enumerator, dev_ctor):
        if index and not isinstance(index, int): raise(ValueError)
        if name and not isinstance(name, str): raise(ValueError)
        if candidates and not isinstance(candidates,list) and not isinstance(candidates,tuple):
            raise(ValueError)
        if (index,name,candidates).count(None) != 2: raise(ValueError)
        if name:
            devNames = enumerator()
            index = devNames.index(name)
        elif candidates:
            devNames = enumerator()
            for c in candidates:
                if c in devNames:
                    index = devNames.index(c)
                    break
            if not index: raise(Exception('device name not found'))   
                
        wr = self.__proc.stdin.write
        wr(cmdHeader)
        wr(b'%X' % index)
        wr(self.__terminator)
        self.__proc.stdin.flush()
        self.__sem_1.acquire()
        hexstr = self.__gResult;
        self.__sem_2.release()
        handle = int_from_hex3(hexstr[0],hexstr[1],hexstr[2])
        #print(handle)
        return dev_ctor(handle)

    def open_input(self,*, index=None, name=None, candidates=None, translate=None):
        if not translate:
            cmd = b'OPEN INPUT '
        elif translate == 8:
            cmd = b'OPEN INPUT8T '
        elif translate == 9:
            cmd = b'OPEN INPUT9T '
        else: raise(ValueError)
        
        return self.__open_io(index, name, candidates, cmd,
                              self.enum_input, MidiInDevice)

    def open_output(self,*, index=None, name=None, candidates=None):
        return self.__open_io(index,name,candidates,b'OPEN OUTPUT ',
                              self.enum_output, MidiOutDevice)

    def close(self, dev):
        if isinstance(dev, MidiInDevice):
            body = b'INPUT %X' % dev.handle
        elif isinstance(dev, MidiOutDevice):
            body = b'OUTPUT %X' % dev.handle
        else:
            raise(ValueError)
        self.__proc.stdin.write(b'CLOSE ')
        self.__proc.stdin.write(body)
        self.__proc.stdin.write(self.__terminator)
        self.__proc.stdin.flush()


    def listen(self, dev):
        if not isinstance(dev, MidiInDevice): raise(ValueError)
        self.__proc.stdin.write(b'LISTEN ')
        self.__proc.stdin.write(b'%X' % dev.handle)
        self.__proc.stdin.write(self.__terminator)
        self.__proc.stdin.flush()

    def send(self, dev, msg):
        if not isinstance(dev, MidiOutDevice): raise(ValueError)
        if isinstance(msg,str): msg = msg.encode()
        elif not isinstance(msg, bytes): raise(ValueError)
        wr = self.__proc.stdin.write
        wr(b'SEND ')
        wr(b'%X ' % dev.handle)
        wr(msg)
        wr(self.__terminator)
        self.__proc.stdin.flush()

    __current_callback_id = 100
    def __generate_callback_id(self):
        self.__current_callback_id += 1
        return self.__current_callback_id

    def register_callback(self, target, signal_pattern, function):
        self.callback(target, signal_pattern, function)
            
    def callback(self, target, signal_pattern, function):
        
        self.__proc.stdin.write(b'CALLBACK ')
        if target is None or target is '*': self.__proc.stdin.write(b'* ')
        elif not isinstance(target, MidiInDevice): raise(ValueError)
        else: self.__proc.stdin.write(b'%X ' % target.handle)
        if not isinstance(signal_pattern, bytes):
            signal_pattern = signal_pattern.encode()
        self.__proc.stdin.write(signal_pattern)
        self.__proc.stdin.write(b' ')
        id = self.__generate_callback_id()
        self.__callback_dic[id] = function
        self.__proc.stdin.write(b'%d' % id)
        self.__proc.stdin.write(self.__terminator)
        self.__proc.stdin.flush()


    def sync(self):
        wr = self.__proc.stdin.write
        wr(b'ECHO SYNC')
        wr(self.__terminator)
        self.__proc.stdin.flush()
        self.__sem_1.acquire()
        s = self.__gResult;
        self.__sem_2.release()
        if b'SYNC' != s:
            raise(Exception('Midiator cannot syncronize'))
        
    def _terminate(self):
        wr = self.__proc.stdin.write
        wr(b'QUIT')
        wr(self.__terminator)
        self.__proc.stdin.flush()
        self.__thread_monitor_stdout.join()
        self.__thread_monitor_stderr.join()


    def stop_process(self):
        self.sync()
        self._terminate()

    def _unsafe_communicate(self, bs):
        self.__proc.stdin.write(bs);
        self.__proc.stdin.write(self.__terminator);
        self.__proc.stdin.flush();

###

MTC = 'mtc'
SONG_POS = 'songpos'
SONG = 'song'
TUNE_REQ = 'tunereq'
EOX = 'eox'
CLOCK = 'clock'
START = 'start'
CONTINUE = 'continue'
STOP = 'stop'
ACTIVE = 'active'
RESET = 'reset'
NOTEOFF = 'noteoff'
NOTEON = 'noteon'
KEYPRESS = 'keypress'
CONTROL = 'control'
PROGRAM = 'program'
PRESSUER = 'pressuer'
BEND = 'bend'

def signal_type(signal):
    h = signal[0]
    if h == 'F':
        return {'1':MTC,'2':SONGPOS,'3':SONG,'6':TUNEREQ,
                '7':EOX,'8':CLOCK,'A':START,'B':CONTINUE,
                'C':STOP,'E':ACTIVE,'F':RESET}[signal[1]]
    else:
        return {'8':NOTEOFF, '9':NOTEON, 'A':KEYPRESS, 'B':CONTROL,
                'C':PROGRAM, 'D':PRESSUER, 'E':BEND}[h]


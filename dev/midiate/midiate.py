# -*- coding: utf-8 -*-

import sys
import subprocess
import threading
import time


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
    r1 = int_from_hex2(b[0],b[1])
    if length == 2: return (r1,)
    else:
        r2 = int_from_hex2(b[2],b[3])
        if length == 4: return (r1,r2)
        else: return (r1,r2,int_from_hex2(b[4],b[5]))

class Midiator():
    def __init__(self):
        self.proc = None
        self.crlf = None
        self.endmsg = None
        self.terminator = None
        self.thread_monitor_stdout = None
        self.thread_monitor_stderr = None
        self.sem_1 = None
        self.sem_2 = None
        self.gResult = None
        self.gError = None
        self.callback_dic = None
        self.prev_dev = None
        self.prev_msg = None
        self.prev_raw_msg = None

    def trunc(self,str):
        return str[0:(-2 if self.crlf else -1)]

    def monitor_stdout(self):
        while True:
            line = self.proc.stdout.readline()
            if line==b'': return
            cmd = line[0];
            if cmd == ord('C'):
                id = decode_callback_id(line,2)
                print('the id=',id)
                function = self.callback_dic[id]
                if self.prev_raw_msg is None: self.prev_raw_msg = decode_to_raw(self.prev_msg)
                function(self.prev_dev, self.prev_msg, self.prev_raw_msg)
            elif   cmd == ord('1'):
                self.prev_dev = take_handle_from_recv_msg(line)
                self.prev_msg = line[6:8]
                self.prev_raw_msg = None
            elif cmd == ord('2'): 
                self.prev_dev = take_handle_from_recv_msg(line)
                self.prev_msg = line[6:10]
                self.prev_raw_msg = None
            elif cmd == ord('3'):
                self.prev_dev = take_handle_from_recv_msg(line)
                self.prev_msg = line[6:12]
                self.prev_raw_msg = None
            elif cmd == ord('{'):
                self.gResult = []
                while True:
                    line = self.proc.stdout.readline()
                    if line != (b'}\r\n' if self.crlf else b'}\n'):
                        self.gResult.append(self.trunc(line).decode())
                    else: break
                self.sem_1.release()
                self.sem_2.acquire()
            elif cmd == ord('<'):
                self.gResult = self.trunc(line[2:])
                self.sem_1.release()
                self.sem_2.acquire()
            elif cmd == ord('!') or cmd == ord('F'):
                self.gResult = None
                self.gError = self.trunc(line[2:])
                #sem_1.release()
                #sem_2.acquire()

            #else:        
            print("[OUT]",line)
            sys.stdout.flush();

    def monitor_stderr(self):
        while True:
            line = self.proc.stderr.readline()
            if line==b'': return
            print("[ERR]",line)
            sys.stdout.flush();

    def _prepare(self):
        self.proc = subprocess.Popen('a:/dropbox/home/git/intermidiator/intermidiator.exe',
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        s_ready = self.proc.stdout.readline();
        if s_ready == b'READY\r\n' : self.crlf, self.terminator = True, b'\r\n'
        elif s_ready == b'READY\n' : self.crlf, self.terminator = False, b'\n'
        else:
            print('ERROR!')
            return False

        #monitor_stdout, monitor_stderr = self.generate_monitors();
        self.thread_monitor_stdout = threading.Thread(target=self.monitor_stdout)
        self.thread_monitor_stderr = threading.Thread(target=self.monitor_stderr)
        self.sem_1 = threading.Semaphore(0)
        self.sem_2 = threading.Semaphore(0)
        self.callback_dic = {}
        return True

    def _start(self):
        self.thread_monitor_stdout.start()
        self.thread_monitor_stderr.start()

    def start_process(self):
        self._prepare()
        self._start()


    def _enum_io(self,cmd):
        self.proc.stdin.write(cmd)
        self.proc.stdin.write(self.terminator)
        self.proc.stdin.flush()
        self.sem_1.acquire()
        names = self.gResult;
        self.sem_2.release()
        return names

    def enum_input(self):
        return self._enum_io(b'LIST INPUT')
    def enum_output(self):
        return self._enum_io(b'LIST OUTPUT')

    def _open_io(self, index, name, cmdHeader, enumerator):
        if index is None and name is None: raise(ValueError)
        elif index is not None and name is not None: raise(ValueError)
        elif name:
            devNames = enumerator()
            index = devNames.index(name)
        wr = self.proc.stdin.write
        wr(cmdHeader)
        wr(b'%X' % index)
        wr(self.terminator)
        self.proc.stdin.flush()
        self.sem_1.acquire()
        hexstr = self.gResult;
        self.sem_2.release()
        handle = int_from_hex3(hexstr[0],hexstr[1],hexstr[2])
        print(handle)
        return handle

    def open_input(self, index=None, name=None):
        return self._open_io(index,name,b'OPEN INPUT ',self.enum_input)

    def open_output(self, index=None, name=None):
        return self._open_io(index,name,b'OPEN OUTPUT ',self.enum_output)

    def listen(self, dev):
        self.proc.stdin.write(b'LISTEN ')
        self.proc.stdin.write(b'%X' % dev)
        self.proc.stdin.write(self.terminator)
        self.proc.stdin.flush()

    def send(self, dev, msg):
        if isinstance(msg,str): msg = msg.encode()
        elif not isinstance(msg, bytes): pass # error
        self.proc.stdin.write(b'SEND ')
        self.proc.stdin.write(b'%X ' % dev)

        self.proc.stdin.write(msg)
        self.proc.stdin.write(self.terminator)
        self.proc.stdin.flush()

    current_callback_id = 100
    def generate_callback_id(self):
        self.current_callback_id += 1
        return self.current_callback_id

    def callback(self, target, signal_pattern, function):
        self.proc.stdin.write(b'CALLBACK ')
        if target is None or target is '*': self.proc.stdin.write(b'* ')
        else: self.proc.stdin.write(b'%X ' % target)
        self.proc.stdin.write(signal_pattern.encode())
        self.proc.stdin.write(b' ')
        id = self.generate_callback_id()
        self.callback_dic[id] = function
        self.proc.stdin.write(b'%d' % id)
        self.proc.stdin.write(self.terminator)
        self.proc.stdin.flush()



    def _terminate(self):
        wr = self.proc.stdin.write
        wr(b'QUIT')
        wr(self.terminator)
        self.proc.stdin.flush()
        self.thread_monitor_stdout.join()
        self.thread_monitor_stderr.join()


    def stop_process(self):
        self._terminate()

    def unsafeCommunicate(self, bs):
        self.proc.stdin.write(bs);
        self.proc.stdin.write(self.terminator);
        self.proc.stdin.flush();

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


# -*- coding: utf-8 -*-
import sys
import subprocess
import threading
import time

proc = None
crlf = None
endmsg = None
terminator = None
thread_monitor_stdout = None
thread_monitor_stderr = None
sem_1 = None
sem_2 = None
gResult = None
gError = None
callback_dic = None

def getdir():
    return __name__

def trunc(str):
    return str[0:(-2 if crlf else -1)]


def chr2hex(ascii):
    if ascii <= 57: return (ascii-48)
    else:           return ascii-65 + 10

def int_from_hex3(c1,c2,c3):
    return (chr2hex(c1)*16+chr2hex(c2))*16+chr2hex(c3)

def int_from_hex2(c1,c2):
    return chr2hex(c1)*16+chr2hex(c2)

def take_handle_from_recv_msg(line):
    return int_from_hex3(line[2],line[3],line[4])

prev_dev = None
prev_msg = None
prev_raw_msg = None

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
        


def monitor_stdout():
    global prev_dev, prev_msg, prev_raw_msg
    while True:
        line = proc.stdout.readline()
        if line==b'': return
        cmd = line[0];
        if cmd == ord('C'):
            id = decode_callback_id(line,2)
            print('the id=',id)
            function = callback_dic[id]
            if prev_raw_msg is None: prev_raw_msg = decode_to_raw(prev_msg)
            function(prev_dev, prev_msg, prev_raw_msg)
        elif   cmd == ord('1'):
            prev_dev = take_handle_from_recv_msg(line)
            prev_msg = line[6:8]
            prev_raw_msg = None
        elif cmd == ord('2'): 
            prev_dev = take_handle_from_recv_msg(line)
            prev_msg = line[6:10]
            prev_raw_msg = None
        elif cmd == ord('3'):
            prev_dev = take_handle_from_recv_msg(line)
            prev_msg = line[6:12]
            prev_raw_msg = None
        elif cmd == ord('{'):
            global gResult
            gResult = []
            while True:
                line = proc.stdout.readline()
                if line != (b'}\r\n' if crlf else b'}\n'):
                    gResult.append(trunc(line).decode())
                else: break
            sem_1.release()
            sem_2.acquire()
        elif cmd == ord('<'):
            gResult = trunc(line[2:])
            sem_1.release()
            sem_2.acquire()
        elif cmd == ord('!') or cmd == ord('F'):
            gResult = None
            gError = trunc(line[2:])
            #sem_1.release()
            #sem_2.acquire()

        #else:        
        print("[OUT]",line)
        sys.stdout.flush();

def monitor_stderr():
    while True:
        line = proc.stderr.readline()
        if line==b'': return
        print("[ERR]",line)
        sys.stdout.flush();

def _prepare():
    global proc
    global crlf, terminator
    global thread_monitor_stdout, thread_monitor_stderr
    global sem_1, sem_2
    global callback_dic
    proc = subprocess.Popen('a:/dropbox/home/git/intermidiator/intermidiator.exe',
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    s_ready = proc.stdout.readline();
    if s_ready == b'READY\r\n' : crlf, terminator = True, b'\r\n'
    elif s_ready == b'READY\n' : crlf, terminator = False, b'\n'
    else:
        print('ERROR!')
        return False

    thread_monitor_stdout = threading.Thread(target=monitor_stdout)
    thread_monitor_stderr = threading.Thread(target=monitor_stderr)
    sem_1 = threading.Semaphore(0)
    sem_2 = threading.Semaphore(0)
    callback_dic = {}
    return True

def _start():
    thread_monitor_stdout.start()
    thread_monitor_stderr.start()

def start_process():
    _prepare()
    _start()

    
def _enum_io(cmd):
    proc.stdin.write(cmd)
    proc.stdin.write(terminator)
    proc.stdin.flush()
    sem_1.acquire()
    names = gResult;
    sem_2.release()
    return names

def enum_input():
    return _enum_io(b'LIST INPUT')
def enum_output():
    return _enum_io(b'LIST OUTPUT')

def _open_io(index, name, cmdHeader, enumerator):
    if index is None and name is None: raise(ValueError)
    elif index is not None and name is not None: raise(ValueError)
    elif name:
        devNames = enumerator();
        index = devNames.index(name)
    wr = proc.stdin.write
    wr(cmdHeader)
    wr(b'%X' % index)
    wr(terminator)
    proc.stdin.flush()
    sem_1.acquire()
    hexstr = gResult;
    sem_2.release()
    handle = int_from_hex3(hexstr[0],hexstr[1],hexstr[2])
    print(handle)
    return handle

def open_input(index=None, name=None):
    return _open_io(index,name,b'OPEN INPUT ',enum_input)

def open_output(index=None, name=None):
    return _open_io(index,name,b'OPEN OUTPUT ',enum_output)

def listen(dev):
    proc.stdin.write(b'LISTEN ')
    proc.stdin.write(b'%X' % dev)
    proc.stdin.write(terminator)
    proc.stdin.flush()

def send(dev, msg):
    if isinstance(msg,str): msg = msg.encode()
    elif not isinstance(msg, bytes): pass # error
    proc.stdin.write(b'SEND ')
    proc.stdin.write(b'%X ' % dev)
    
    proc.stdin.write(msg)
    proc.stdin.write(terminator)
    proc.stdin.flush()
    
current_callback_id = 100
def generate_callback_id():
    global current_callback_id
    current_callback_id += 1
    return current_callback_id
    
def callback(target, signal_pattern, function):
    proc.stdin.write(b'CALLBACK ')
    if target is None or target is '*': proc.stdin.write(b'* ')
    else: proc.stdin.write(b'%X ' % target)
    proc.stdin.write(signal_pattern.encode())
    proc.stdin.write(b' ')
    id = generate_callback_id()
    callback_dic[id] = function
    proc.stdin.write(b'%d' % id)
    proc.stdin.write(terminator)
    proc.stdin.flush()



def _terminate():
    wr = proc.stdin.write
    wr(b'QUIT')
    wr(terminator)
    proc.stdin.flush()
    thread_monitor_stdout.join()
    thread_monitor_stderr.join()


def stop_process():
    _terminate()

def unsafeCommunicate(bs):
    proc.stdin.write(bs);
    proc.stdin.write(terminator);
    proc.stdin.flush();

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


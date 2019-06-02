import hashlib
import os
import socket
import time
from tkinter import Tk
from tkinter import filedialog


def suffix(size):
    k = 1024
    m = 1024 * k
    g = 1024 * m
    if size < k:
        return str(size) + ' B'
    elif size < m:
        return '{:.2f}'.format(size / k) + ' KB'
    elif size < g:
        return '{:.2f}'.format(size / m) + ' MB'
    else:
        return '{:.2f}'.format(size / g) + ' GB'


root = Tk()
root.withdraw()

HOST = ''
PORT = 23333
BUFSIZE = 1024
SPEEDRATE = 0.333

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen(5)

try:
    while True:
        print('waiting for connection...')

        (c, addr) = s.accept()
        print('receive a file from', addr[0], ':')

        try:
            fname = c.recv(BUFSIZE).decode('utf-8')
            print('received file name :', fname)

            fsize = int(str(c.recv(BUFSIZE).decode('utf-8')))
            print('received file size :', suffix(fsize))

            recvhash = c.recv(BUFSIZE).decode('utf-8')
            print('received file SHA-1 :', recvhash)

        except (ValueError, ConnectionError):
            print('transmission failed : argument initialization failed')
            c.close()
            print()
            continue

        fpath = filedialog.askdirectory(title='Save', initialdir=os.getcwd()) + '/' + fname
        f = open(fpath, 'wb')
        print('destination path :', fpath)

        rsize = 0
        per = 0
        speed = 0
        t0 = time.perf_counter()

        try:
            while not rsize == fsize:
                t2 = time.perf_counter()
                if fsize - rsize > BUFSIZE:
                    data = c.recv(BUFSIZE)
                    f.write(data)
                else:
                    data = c.recv(fsize - rsize)
                    f.write(data)
                rsize += len(data)
                t3 = time.perf_counter()
                dt = t3 - t2
                s0 = speed
                speed = len(data) / dt
                if s0 and abs((speed - s0) / s0) > SPEEDRATE:
                    speed = s0
                print('\r', '{:.2f}'.format(rsize / fsize * 100), '%', suffix(speed), '/ s', end='')

        except ConnectionError:
            print()
            f.close()
            os.remove(fpath)
            print('transmission failed : client connection interrupted')
            c.close()
            print()
            continue

        print()
        t1 = time.perf_counter()
        dt = t1 - t0
        speed = fsize / dt
        print('total time :', '{:.6f}'.format(dt), 's')
        print('average speed :', suffix(speed), '/ s')
        f.close()

        f = open(fpath, 'rb')
        calchash = hashlib.sha1()
        while True:
            data = f.read(BUFSIZE)
            if not data:
                break
            calchash.update(data)
        calchash = str(calchash.hexdigest())
        print('calculated file SHA-1 :', calchash)
        f.close()
        if recvhash == calchash:
            print('data check succeeded')
            print('transmission succeeded')
            c.sendall('transmission succeeded'.encode('utf-8'))
        else:
            os.remove(fpath)
            print('transmission failed : data check failed')
            c.sendall('transmission failed : data check failed'.encode('utf-8'))

        c.close()
        print()

except KeyboardInterrupt:
    print()
    print('transmission failed : server closed')
    exit()

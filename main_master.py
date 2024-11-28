from time import sleep
from os import mkdir
from datetime import datetime as dt
from Sound import Sound  # 音声系ラッパー
from Video import Video  # 映像系ラッパー
from temp import Cpu_percent  # リソースモニタラッパー
from re import fullmatch
# from LED_module import *
import bluetooth as BT
from subprocess import getstatusoutput
from threading import Thread
from sys import exit
from socket import gethostname

class Device:
    def __init__(self, name, addr, port):
        self.name = name
        self.addr = addr
        self.port = port
        self.sock = None
        self.delay = 0.

def main():
    # 準備
    device_name = 'p01'
    devices = [
        Device('poezo02', 'DC:A6:32:8A:95:07', 1),
        # Device('porzo03', 'D8:3A:DD:27:16:5A', 1)
    ]
    video_rate = 10  # ビデオ録画フレームレート
    sound_rate = 48000  # サウンド録音サンプリングレート
    # recLED = ControlledLED(27, [0.1, 0.9])
    # readyLED = ControlledLED(10, [1.0, 0.0])

    try:
        for device in devices:
            device.sock = BT.BluetoothSocket(BT.RFCOMM)
            device.sock.connect((device.addr, device.port))
            print(f'{device.name} connected')
    except Exception as e:
        print(e)
        exit()

    waitResponsies([device.sock for device in devices], 'piezo_OK', 32)

    threads = []
    for device in devices:
        thread = Thread(target=delayCheck, args=(device.sock, [device.delay]))
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join()


    while True:
        print('prease recording time >', end='')
        time = input()
        try:
            time = int(time)
            break
        except Exception:
            print('try again')
            continue

    for device in devices:
        device.sock.send('piezo_time:' + str(time))

    waitResponsies([device.sock for device in devices], 'time_OK', 32)

    for device in devices:
        device.sock.send('piezo_ready')

    # 音声、ビデオ、リソースモニタの準備
    sound = Sound(chunksize=1024, nchannels=1, fs=sound_rate)
    video = Video(reso=(1280, 720), framerate=video_rate, hflip=False, vflip=False)
    percent = Cpu_percent(10)
    print('初期化完了')
    video.preview(x=1920//2, y=1080//2, w=1920//2, h=1080//2)

    sleep(3)
    
    waitResponsies([device.sock for device in devices], 'piezo_ready', 32)

    for device in devices:
        device.sock.send('piezo_start')

    # 録音開始
    print('録音開始')
    path = dt.now().strftime('%y%m%d%H%M') + gethostname() # 現在時刻からフォルダ名を生成
    mkdir(path)  # フォルダを作成
    percent.startClock(path)
    sound.startRecord(f'{path}/sound_{sound_rate}hz')
    video.startRecord(f'{path}/video_{video_rate}fps')

    sleep(time)

    # 録音終了
    video.stopRecord()
    sound.endRecord()
    percent.end()
    print('録音終了')

    for device in devices:
        device.sock.send('piezo_end')
    waitResponsies([device.sock for device in devices], 'end_OK', 32)
    sleep(3)
    print('処理が完了しました')

def delayCheck(socket, med, intarval=.5, loop=31):
    delays = []
    for _ in range(loop):
        now = dt.now()
        socket.send('delayCheck')
        socket.recv(64)
        delays.append(((dt.now() - now).microseconds)/1000)
        sleep(intarval)
    med[0] = sort(delays)[len(delays)//2-1]

def waitResponse(socket, msg, backLog=1024):
    while True:
        data = socket.recv(backLog).decode()
        print(data, msg)
        if data == msg:
            break

def waitResponsies(sockets, msg, backLog=1024):
    threads = []
    for socket in sockets:
        t = Thread(target=waitResponse, args=(socket, msg, backLog))
        t.start()
        threads.append(t)
    
    for t in threads:
        t.join()

def sort(array):
    if len(array) <= 1:
        return array
    left = []
    right = []
    mid = array[0]
    for i in range(1, len(array)):
        if mid > array[i]:
            left.append(array[i])
        else:
            right.append(array[i])
    left = sort(left)
    right = sort(right)
    return left + [mid] + right

if __name__ == '__main__': main()
from time import sleep
from os import mkdir
from datetime import datetime as dt
from Sound import Sound # 音声系ラッパー
from Video import Video # 映像系ラッパー
from temp import Cpu_percent # リソースモニタラッパー
from re import fullmatch
# from LED_module import *
import bluetooth as BT
from socket import gethostname


def main():
    # initialize
    video_rate = 10
    sound_rate = 48000
    # recLED = ControlledLED(27, [0.1, 0.9])
    # readyLED = ControlledLED(10, [1,0])
    backLog = 64
    
    readyFlg:bool = False
    time:int = None
    sound:Sound = None
    video:Video = None
    percent:Cpu_percent = None
    btSocket:BT.BluetoothSocket = None
    master_socket:BT.BluetoothSocket = None

    while True:
        if master_socket == None:
            # BT listen
            btSocket = BT.BluetoothSocket(BT.RFCOMM)
            btSocket.bind(("", BT.PORT_ANY))
            btSocket.listen(1)
            print(f'channel {btSocket.getsockname()[1]}')
            print(f'{BT.read_local_bdaddr()[0]}')
            master_socket, master_info = btSocket.accept()
            print(f'connected {master_info}')
            master_socket.send('piezo_OK')
            continue

        recv = master_socket.recv(backLog).decode()
        print(f'get: {recv}')
        if 'time' in recv:
            try:
                time = int(recv.split(':')[1])
            except Exception as e:
                print('bluetooth error')
                print(e)
                master_socket.send('time_error')
                continue
            print('record time: ' + str(time))
            master_socket.send('time_OK')

        elif 'delayCheck' in recv:
            master_socket.send('piezo_delayCheck')
            print('delay_check')

        elif 'start' in recv:
            if readyFlg == False:
                master_socket.send('did_not_ready')
                print('did not ready error')
                continue
            mkdir(path)
            percent.startClock(path)
            sound.startRecord(f'{path}/sound_{sound_rate}hz')
            video.startRecord(f'{path}/video_{video_rate}fps')
            print('record start')
            
            sleep(time)

            sound.endRecord()
            video.stopRecord()
            percent.end()
            video.stopPreview()
            print('record end')
            readyFlg = False

        elif 'ready' in recv:
            sound = Sound(chunksize=1024, nchannels=1, fs=sound_rate)
            video = Video(reso=(1280, 720), framerate=video_rate, hflip=False, vflip=False)
            percent = Cpu_percent(10)
            video.preview(x=1920//2, y=1080//2, w=1920//2, h=1080//2)
            path = dt.now().strftime('%y%m%d_%H%M_') + gethostname()
            master_socket.send('piezo_ready')
            readyFlg = True
            
            print('ready')

        elif 'piezo_end' in recv:
            master_socket.send('end_OK')
            master_socket.close()
            btSocket.close()
            master_socket = None
            btSocket = None
            del video
            del sound
            del percent
        
        else:
            print('unknown message: ' + recv)

    '''
    # ready
    time = int(master_socket.recv(16))
    sound = Sound(chunksize=1024, nchannels=1, fs=sound_rate)
    video = Video(reso=(1280, 720), framerate=video_rate, hflip=False, vflip=False)
    percent = Cpu_percent(10)
    # readyLED.blink()
    print('ready')
    video.preview(x=1920//2, y=1080//2, w=1920//2, h=1080//2)
    master_socket.send('piezo_ready')
    
    waitRecvStr(master_socket, 'piezo_start', 16)

    # Recording
    path = dt.now().strftime('%y%m%d%H%M') + '01'
    mkdir(path)
    percent.startClock(path)
    sound.startRecord(f'{path}/sound_{sound_rate}hz')
    video.startRecord(f'{path}/video_{video_rate}fps')
    # readyLED.stop()
    # recLED.blink()
    master_socket.close()
    btSocket.close()
    print('Recording')

    sleep(time)
        
    video.stopRecord()
    sound.endRecord()
    percent.end()
    video.stopPreview()
    # recLED.stop()
    print('record end')
    # 終了処理終わり
    
    print('Compleated')

def waitRecvStr(socket, msg, backLog=1024):
    while True:
        data = socket.recv(backLog).decode()
        if data == msg:
            return
    '''

if __name__ == '__main__': main()

#!/usr/bin/env python3

import os
import sys
import queue
from subprocess import Popen, PIPE
from threading import Thread
from time import sleep

import av

currentdir = os.path.dirname(os.path.abspath(__file__))
parentdir = os.path.abspath(os.path.join(currentdir, os.pardir))
sys.path.insert(0, parentdir)


# main decoding thread
class Decode(Thread):
    def __init__(self, input):
        Thread.__init__(self)
        self.input = input
        self.w = 1024
        self.h = 576
        self.fps = 25

        self.fifo = queue.Queue(maxsize=100)

    def run(self):
        for input in self.input:
            container = av.open(input, 'r')

            resampler = av.AudioResampler(
                format=av.AudioFormat('s16'),
                layout=2,
                rate=44100,
            )

            for packet in container.demux():
                for frame in packet.decode():
                    type = packet.stream.type

                    video_frame = None
                    audio_frame = None

                    if type == 'video':
                        new_v_frame = frame.reformat(self.w, self.h, 'rgb24')
                        new_v_frame.pts = None
                        video_frame = new_v_frame.planes[0].to_bytes()

                    if type == 'audio':
                        frame.pts = None
                        new_a_frame = resampler.resample(frame)
                        audio_frame = new_a_frame.planes[0].to_bytes()

                    self.fifo.put([video_frame, audio_frame])


dec = Decode([
    'test_clips/waves.mp4',
    'test_clips/test.mp4',
    'test_clips/water.mp4',
    'test_clips/test.mp4'
 ])
dec.setDaemon(True)
dec.start()

sleep(1)

play = None

while True:
    try:
        v = dec.fifo.get(block=True, timeout=2)
        if not play:
            cmd = [
                'ffplay',
                '-f', 'rawvideo',
                '-pixel_format', 'rgb24',
                '-video_size', '1024x576',
                # '-f', 's16le',
                # '-ar', '44100',
                # '-ac', '2',
                '-i', '-',
                ]
            play = Popen(cmd, stdin=PIPE)
        try:
            if v[0] is not None:
                play.stdin.write(v[0])
        except IOError as e:
            print(e)
            break
    except queue.Empty:
        play.kill()
        print("empty")
        break

print("\ndone!")

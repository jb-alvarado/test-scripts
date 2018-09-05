#!/usr/bin/env python3

import os
import sys
import queue
from subprocess import Popen, PIPE
from time import sleep

currentdir = os.path.dirname(os.path.abspath(__file__))
parentdir = os.path.abspath(os.path.join(currentdir, os.pardir))
sys.path.insert(0, parentdir)

from decoder import Decode

decode = Decode(
    ['test_clips/test.mp4',
     'test_clips/waves.mp4',
     'test_clips/water.mp4',
     'test_clips/test.mp4'
     ], 1024, 576, 44100)

decode.setDaemon(True)
decode.start()

sleep(1)

play = None

while True:
    try:
        frame = decode.fifo.get(block=True, timeout=0.8)
        if not play:
            cmd = [
                'ffplay',
                # '-f', 'rawvideo',
                # '-pixel_format', 'rgb24',
                # '-video_size', '1024x576',
                '-f', 's16le',
                '-ar', '44100',
                '-ac', '2',
                '-i', 'pipe:0',
                ]
            play = Popen(cmd, stdin=PIPE)
        try:
            if frame[1] is not None:
                play.stdin.write(frame[1].to_bytes())
            # sleep(0.04)
            # play.stdin.write(a.to_bytes())
        except IOError as e:
            print(e)
            exit()
    except queue.Empty:
        play.kill()
        break

print("\ndone!")

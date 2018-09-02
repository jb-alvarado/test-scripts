#!/usr/bin/env python3

import os
import sys
from subprocess import Popen, PIPE
from time import sleep

currentdir = os.path.dirname(os.path.abspath(__file__))
parentdir = os.path.abspath(os.path.join(currentdir, os.pardir))
sys.path.insert(0, parentdir)

from decoder import Decode

decode = Decode('test_clips/test.mp4', 1024, 576)
decode.start()

sleep(1)

play = None

while decode.v_fifo:
    v = decode.v_fifo.pop()
    a = decode.a_fifo.pop()
    if not play:
        cmd = [
            'ffplay',
            '-f', 'rawvideo',
            '-pixel_format', 'rgb24',
            '-video_size', '1024x576',
            # '-f', 's16le',
            # '-ar', '44100',
            # '-ac', '2',
            '-i', 'pipe:0',
            ]
        play = Popen(cmd, stdin=PIPE)
    try:
        play.stdin.write(v.to_bytes())
        # play.stdin.write(a.to_bytes())
    except IOError as e:
        print(e)
        exit()

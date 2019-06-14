#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from subprocess import Popen, PIPE, TimeoutExpired
from time import sleep
from threading import Thread
from queue import Queue
from shutil import copyfileobj


class CheckLiveStream(Thread):
    def __init__(self):
        Thread.__init__(self)

        self.live_is_running = False

        self.cmd = [
            'ffmpeg', '-v', 'error', '-hide_banner', '-nostats',
            '-i', 'rtmp://localhost/live/stream', '-c', 'copy',
            '-f', 'mpegts', '-']

    def run(self):
        while True:
            proc = Popen(self.cmd, stdout=PIPE, stderr=PIPE)

            try:
                stdout, error = proc.communicate(timeout=2)
            except TimeoutExpired:
                proc.kill()
                stdout, error = proc.communicate()

            if stdout:
                print('livestream found')
                self.live_is_running = True
            else:
                print('no livestream')
                self.live_is_running = False


if __name__ == '__main__':
    buffer = Queue()
    check = CheckLiveStream()
    check.daemon = True

    check.start()

    dec_cmd = [
        'ffmpeg', '-hide_banner', '-nostats', '-v', 'error',
        '-i', 'rtmp://localhost/live/stream',
        '-r', '25', '-s', '1024x576',
        '-c:v', 'mpeg2video', '-intra', '-b:v', '50M',
        '-minrate', '50M', '-maxrate', '50M', '-bufsize', '50M',
        '-c:a', 's302m', '-strict', '-2', '-ar', '48k', '-ac', '2',
        '-f', 'mpegts', '-']

    enc_cmd = [
        'ffplay', '-v', 'error', '-hide_banner', '-nostats',
        '-i', 'pipe:0']

    encoder = Popen(enc_cmd, stderr=None, stdin=PIPE, stdout=None)

    while True:
        if check.live_is_running:
            with Popen(dec_cmd, stdout=PIPE) as decoder:
                copyfileobj(decoder.stdout, encoder.stdin)

        sleep(1)

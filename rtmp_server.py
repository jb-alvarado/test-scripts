#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from subprocess import Popen, PIPE, TimeoutExpired
from threading import Thread
from shutil import copyfileobj
from queue import Queue


class RtmpServer(Thread):
    def __init__(self, pid, live, buffer):
        Thread.__init__(self)

        self._pid = pid
        self._live = live
        self._buffer = buffer
        self.proc = None
        self.is_running = True
        self.cmd = [
            'ffmpeg', '-v', 'error', '-hide_banner', '-nostats', '-f', 'flv',
            '-listen', '1', '-i', 'rtmp://localhost/live/test',
            '-r', '25', '-s', '1024x576',
            '-c:v', 'mpeg2video', '-intra', '-b:v', '50M',
            '-minrate', '50M', '-maxrate', '50M', '-bufsize', '50M',
            '-c:a', 's302m', '-strict', '-2', '-ar', '48k', '-ac', '2',
            '-f', 'mpegts', '-']

    def run(self):
        while self.is_running:
            self.proc = Popen(self.cmd, stdout=PIPE)

            while self.proc.poll() is None:
                data = self.proc.stdout.read(65424)
                self._buffer.put(data)

    def stop(self):
        self.proc.terminate()
        self.is_running = False


if __name__ == '__main__':
    buffer = Queue()
    server = RtmpServer(1234, 'live', buffer)
    server.daemon = True

    server.start()

    try:
        play = [
            'ffplay', '-v', 'error', '-hide_banner', '-nostats',
            '-i', 'pipe:0']

        encoder = Popen(play, stderr=None, stdin=PIPE, stdout=None)

        while True:
            data = buffer.get()
            if data:
                encoder.stdin.write(data)
    except KeyboardInterrupt:
        server.stop()

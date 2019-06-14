#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
from threading import Thread
from subprocess import Popen, PIPE
from queue import Queue


SOURCES = [
    "/Users/user/DEV/watch/intro.mp4",
    "/Users/user/DEV/watch/test.mp4"
]


class Player(Thread):
    def __init__(self, buffer):
        Thread.__init__(self)

        self._buffer = buffer
        self.decoder = None
        self.index = 0
        self.is_running = True

    def play(self):
        while True:
            if self.is_running:
                self.decoder = Popen([
                    'ffmpeg', '-hide_banner', '-v', 'error', '-nostats',
                    '-i', SOURCES[self.index], '-r', '25', '-s', '1024x576',
                    '-c:v', 'mpeg2video', '-intra', '-b:v', '50M',
                    '-minrate', '50M', '-maxrate', '50M', '-bufsize', '50M',
                    '-c:a', 's302m', '-strict', '-2', '-ar', '48k',
                    '-ac', '2', '-f', 'mpegts', '-'], stdout=PIPE)

                print('Play:', SOURCES[self.index])

                while self.decoder.poll() is None:
                    data = self.decoder.stdout.read(65424)
                    self._buffer.put(data)

                self.index += 1
            else:
                time.sleep(0.5)

    run = play

    def stop_decoder(self):
        self.decoder.terminate()
        self.is_running = False


class Inject(Thread):
    def __init__(self, buffer):
        Thread.__init__(self)

        self._buffer = buffer
        self.decoder = None
        self.index = 0
        self.is_running = True

    def play(self):
        while True:
            if self.is_running:
                print('Play:', SOURCES[-1])
                self.decoder = Popen([
                    'ffmpeg', '-hide_banner', '-nostats', '-v', 'error',
                    '-i', SOURCES[-1], '-r', '25', '-s', '1024x576',
                    '-c:v', 'mpeg2video', '-intra', '-b:v', '50M',
                    '-minrate', '50M', '-maxrate', '50M', '-bufsize', '50M',
                    '-c:a', 's302m', '-strict', '-2', '-ar', '48k', '-ac', '2',
                    '-f', 'mpegts', '-'], stdout=PIPE)

                while self.decoder.poll() is None:
                    data = self.decoder.stdout.read(65424)
                    self._buffer.put(data)

                self._buffer.put(None)
                self.is_running = False
            else:
                time.sleep(0.5)

    run = play


def main():
    buffer = Queue(maxsize=48)
    """
    play = [
        'ffplay', '-v', 'error', '-hide_banner', '-nostats',
        '-i', 'pipe:0']
    """
    stream = ['ffmpeg', '-v', 'info', '-hide_banner', '-nostats', '-re',
              '-thread_queue_size', '256', '-i', 'pipe:0', '-c:v', 'libx264',
              '-crf', '23', '-x264opts', 'keyint=50:min-keyint=50:no-scenecut',
              '-maxrate', '1300k', '-bufsize', '2600k', '-preset', 'medium',
              '-profile:v', 'Main', '-level', '3.1', '-refs', '3',
              '-c:a', 'libfdk_aac', '-ar', '44100', '-b:a', '128k',
              '-flags', '+global_header', '-f', 'flv',
              'rtmp://localhost/live/stream']
    try:
        encoder = Popen(stream, stderr=None, stdin=PIPE, stdout=None)

        play_thread = Player(buffer)
        play_thread.daemon = True
        play_thread.start()

        inject_thread = Inject(buffer)
        inject_thread.daemon = True

        counter = 0

        while True:
            data = buffer.get()
            print("Counter: {}".format(counter), end="\r")
            counter += 1
            if data is None:
                play_thread.is_running = True
            else:
                encoder.stdin.write(data)

            if counter == 300:
                print("switch source")
                play_thread.stop_decoder()
                inject_thread.start()

    finally:
        encoder.wait()


if __name__ == '__main__':
    main()

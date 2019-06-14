#!/usr/bin/env python3

import queue
from threading import Thread
from time import sleep


class Fill(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.fifo = queue.Queue(maxsize=10)

    def run(self):
        for i in range(100):
            if i % 2 == 0:
                a = i

            self.fifo.put('a: {} | b: {}'.format(a, i))

            sleep(0.2)


filler = Fill()

filler.setDaemon(True)
filler.start()

sleep(0.2)

while True:
    try:
        a = filler.fifo.get(block=True, timeout=0.5)

        print(a)
    except queue.Empty:
        break

print("done!")

#!/usr/bin/env python3

import queue
from threading import Thread
from time import sleep

FIFO = queue.Queue(maxsize=10)


class Fill(Thread):
    def __init__(self):
        Thread.__init__(self)

    def run(self):
        for a in range(3):
            for i in range(100):
                FIFO.put([a, i])
                sleep(0.009)

        FIFO.task_done()


filler = Fill()

filler.setDaemon(True)
filler.start()

sleep(0.2)

while True:
    try:
        num = FIFO.get(block=True, timeout=0.5)
        sleep(0.005)
        print('{}'.format(num))
    except queue.Empty:
        break

print("done!")

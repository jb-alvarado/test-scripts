#!/usr/bin/env python3

# This file is part of ffplayout-engine
#
# ffplayout-engine is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ffplayout-engine is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ffplayout-engine. If not, see <http://www.gnu.org/licenses/>.

# ------------------------------------------------------------------------------

import queue
from threading import Thread
from time import sleep

import av

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


# main decoding thread
class Encode(Thread):
    def __init__(self):
        Thread.__init__(self)

        with open('test_scripts/url.txt', 'r') as f:
            self.url = f.readline().strip()

    def run(self):
        output = av.open(self.url, mode='w', format='flv')
        ovstream = output.add_stream('libx264', '25')
        ovstream.options = {"fflags": "+genpts", "preset": "medium", "crf": "22"}
        # ovstream.pix_fmt = 'yuv420p'
        ovstream.width = 1024
        ovstream.height = 576

        while True:
            try:
                frame = decode.fifo.get(block=True, timeout=0.8)

                if frame[0] is not None:
                    try:
                        pkt = ovstream.encode(frame[0])
                    except Exception as e:
                        print(e)
                        return False
                    if pkt is not None:
                        try:
                            output.mux(pkt)
                        except Exception as e:
                            # print(e)
                            # print('mux failed: ' + str(pkt))
                            continue
                    sleep(0.04)
            except queue.Empty:
                output.close()
                break

        print("\ndone!")


Encode().setDaemon(True)
Encode().start()

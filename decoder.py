# This file is part of ffplayout
#
# ffplayout is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ffplayout is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ffplayout. If not, see <http://www.gnu.org/licenses/>.

# ------------------------------------------------------------------------------


import av
from queue import Queue
from threading import Thread

V_FIFO = Queue(maxsize=300)
A_FIFO = Queue(maxsize=300)


# main decoding thread
class Decode(Thread):
    def __init__(self, input, width, height):
        Thread.__init__(self)
        self.input = input
        self.w = width
        self.h = height

        self.resampler = av.AudioResampler(
            format=av.AudioFormat('s16'),
            layout=2,
            rate=44100,
        )

    def run(self):
        for input in self.input:
            container = av.open(input, 'r')

            for packet in container.demux():
                if packet.stream.type == 'video':
                    for v_frame in packet.decode():
                        v_frame.pts = None
                        new_v_frame = v_frame.reformat(self.w, self.h, 'rgb24')
                        V_FIFO.put(new_v_frame.planes[0])
                if packet.stream.type == 'audio':
                    for a_frame in packet.decode():
                        a_frame.pts = None
                        new_a_frame = self.resampler.resample(a_frame)
                        A_FIFO.put(new_a_frame.planes[0])

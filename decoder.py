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
from collections import deque
from threading import Thread


# main decoding thread
class Decode(Thread):
    def __init__(self, input, width, height):
        Thread.__init__(self)
        self.container = av.open(input, 'r')
        self.w = width
        self.h = height
        self.v_fifo = deque()
        self.a_fifo = deque()

        self.resampler = av.AudioResampler(
            format=av.AudioFormat('s16'),
            layout=2,
            rate=44100,
        )

    def run(self):
        for packed in self.container.demux():
            if packed.stream.type == 'video':
                for v_frame in packed.decode():
                    new_frame = v_frame.reformat(self.w, self.h, 'rgb24')
                    self.v_fifo.appendleft(new_frame.planes[0])
            if packed.stream.type == 'audio':
                for a_frame in packed.decode():
                    a_sample = self.resampler.resample(a_frame)
                    self.a_fifo.appendleft(a_sample.planes[0])

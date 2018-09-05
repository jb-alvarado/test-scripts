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

from queue import Queue
from threading import Thread

import av


# main decoding thread
class Decode(Thread):
    def __init__(self, input, width, height, audio_rate=44100):
        Thread.__init__(self)
        self.input = input
        self.w = width
        self.h = height
        self.audio_rate = audio_rate

        # set global fifo buffer
        # it must hold the content while the loop runs over the input files
        self.fifo = Queue(maxsize=100)

    def run(self):
        for input in self.input:
            container = av.open(input, 'r')

            # resample audio line to the given format
            resampler = av.AudioResampler(
                format=av.AudioFormat('s16'),
                layout=2,
                rate=self.audio_rate,
            )

            # loop over the container
            for packet in container.demux():
                type = packet.stream.type

                for frame in packet.decode():
                    video_frame = None
                    audio_frame = None

                    if type == 'video':
                        frame.pts = None
                        new_v_frame = frame.reformat(self.w, self.h, 'rgb24')
                        video_frame = new_v_frame.planes[0]

                    if type == 'audio':
                        frame.pts = None
                        new_a_frame = resampler.resample(frame)
                        audio_frame = new_a_frame.planes[0]

                    # push to fifo buffer
                    self.fifo.put([video_frame, audio_frame])

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

from PIL import Image
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
        self.new_vid_pts = 0

        # set global fifo buffer
        # it must hold the content while the loop runs over the input files
        self.fifo = Queue(maxsize=100)

    def demultiplexer(self, container):
        # resample audio line to the given format
        resampler = av.AudioResampler(
            format=av.AudioFormat('s16'),
            layout=2,
            rate=self.audio_rate,
        )

        # loop over the container
        for packet in container.demux():
            type = packet.stream.type
            # orig_fps = packet.stream.rate

            for frame in packet.decode():
                # current time in video clip
                # timestamp = float(frame.pts * packet.stream.time_base)

                video_frame = None
                audio_frame = None

                if type == 'video':
                    # print('video pts: {}'.format(frame.pts))
                    frame.pts = self.new_vid_pts
                    new_v_frame = frame.reformat(self.w, self.h, 'yuv420p')
                    video_frame = new_v_frame

                    self.new_vid_pts += 512

                if type == 'audio':
                    # print('audio pts: {}'.format(frame.pts))
                    frame.pts = None
                    new_a_frame = resampler.resample(frame)
                    audio_frame = new_a_frame

                # push to fifo buffer
                self.fifo.put([video_frame, audio_frame])
                # self.last_pts += last_vid_pts

    def run(self):
        for input in self.input:
            if input is not None:
                container = av.open(input, 'r')

                self.demultiplexer(container)
            else:
                black = (0, 0, 0)
                img = Image.new('RGB', [self.w, self.h], black)

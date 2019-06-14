#!/usr/bin/env python3

import os
import time
import av

dir_path = os.path.dirname(os.path.realpath(__file__))

output = av.open('remux.mp4', 'w')

out_stream_v = output.add_stream('libx264', 25)
out_stream_a = output.add_stream('aac', rate=44100)
out_stream_v.width = 1024
out_stream_v.height = 576
out_stream_v.options = {'preset': 'faster', 'crf': '24', 'g': '25'}
out_stream_a.options = {'bit_rate': '128k'}

clip = 'test.mp4'
input = av.open(os.path.join(dir_path, os.pardir, 'test_clips', clip))

start = time.time()

new_v_pts = 0
new_a_pts = 0

for packet in input.demux(video=0, audio=0):
    if packet.dts is None:
        continue

    type = packet.stream.type

    for frame in packet.decode():
        if type == 'video':
            print(type, frame.time)
            frame.pts = new_v_pts
            frame.pict_type = 0
            packet = out_stream_v.encode(frame)
            new_v_pts += 512
        elif type == 'audio':
            print(type, frame.time)

            frame.pts = new_a_pts
            packet = out_stream_a.encode(frame)
            new_a_pts += 1024

        output.mux(packet)

end = time.time()

print(end - start)

output.close()

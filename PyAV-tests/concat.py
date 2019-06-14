#!/usr/bin/env python3

import os
import datetime

import av

dir_path = os.path.dirname(os.path.realpath(__file__))

output = av.open('concat.mp4', 'w')

out_stream_v = output.add_stream('libx264', 25)
out_stream_a = output.add_stream('aac', 44100)
out_stream_v.width = 1024
out_stream_v.height = 576
out_stream_v.options = {'preset': 'faster', 'crf': '23', 'g': '25'}
out_stream_a.options = {'bit_rate': '128k'}


list = [
    'thee.mp4',
    'retter.mp4',
    'segen.mp4',
    'test2.mp4',
]

new_video_pts = 0
old_video_pts = 0
new_audio_pts = 0

print(str(datetime.datetime.now()))

for clip in list:
    input_ = av.open(os.path.join(dir_path, os.pardir, 'test_clips', clip))
    input_.options = {}
    print(input_)

    in_stream_v = input_.streams.video[0]
    in_stream_a = input_.streams.audio[0]

    first_pkt = True

    for packet in input_.demux(in_stream_v, in_stream_a):
        if packet.dts is None:
            continue

        type = packet.stream.type

        for frame in packet.decode():
            if type == 'video':
                frame.time_base = '1/12800'
                frame.pts = new_video_pts
                frame.pict_type = 0
                new_v_frame = frame.reformat(1024, 576, 'yuv420p')
                packet = out_stream_v.encode(new_v_frame)

                new_video_pts += 512
            elif type == 'audio':
                frame.time_base = '1/44100'
                frame.pts = new_audio_pts
                packet = out_stream_a.encode(frame)

                new_audio_pts += 1024

            output.mux(packet)

output.close()

print(str(datetime.datetime.now()))

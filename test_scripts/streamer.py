#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import av

container = av.open('test_clips/test.mp4', 'r')

with open('test_scripts/url.txt', 'r') as f:
    url = f.readline().strip()

url = 'test_clips/encode.mp4'

output = av.open(url, mode='w', format='flv')
output_video_stream = output.add_stream('libx264', '25')
output_audio_stream = output.add_stream('aac')

output_video_stream.options = {'preset': 'faster', 'crf': '24'}
output_video_stream.width = 512
output_video_stream.height = 288

for packet in container.demux():
    type = packet.stream.type

    for frame in packet.decode():
        # frame.pts = None
        if type == 'video':
            v_pkt = output_video_stream.encode(frame)
            if v_pkt:
                output.mux(v_pkt)

        if type == 'audio':
            frame.pts = None
            a_pkt = output_audio_stream.encode(frame)

            if a_pkt:
                output.mux(a_pkt)

# Finally we need to flush out the frames that are buffered in the encoder.
if output_audio_stream:
    while True:
        output_packet = output_audio_stream.encode(None)
        if output_packet:
            output.mux(output_packet)
        else:
            break

output.close()

print('Done!')

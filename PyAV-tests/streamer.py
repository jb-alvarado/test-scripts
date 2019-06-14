#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import av

container = av.open('test_clips/test.mp4', 'r')

with open('test_scripts/url.txt', 'r') as f:
    url = f.readline().strip()

url = 'test_clips/encode.mp4'

input_video_stream =  next((s for s in container.streams if s.type == 'video'), None)
input_audio_stream = next((s for s in container.streams if s.type == 'audio'), None)

output_file = av.open(url, mode='w', format='flv')
output_video_stream = output_file.add_stream('libx264', 25)
output_audio_stream = output_file.add_stream('aac')

output_video_stream.width = 512
output_video_stream.height = 288
output_video_stream.options = {'preset': 'faster', 'crf': '24'}
output_audio_stream.options = {}

for packet in container.demux([s for s in (input_video_stream, input_audio_stream) if s]):
    type = packet.stream.type

    for frame in packet.decode():
        frame.pts = None
        if type == 'video':
            v_pkt = output_video_stream.encode(frame)
            if v_pkt:
                output_file.mux(v_pkt)


"""
frame.pts = None
output_packets = [output_audio_stream.encode(frame)]
while output_packets[-1]:
    output_packets.append(output_audio_stream.encode(None))

for p in output_packets:
    if p:
        output.mux(p)

# Finally we need to flush out the frames that are buffered in the encoder.
if output_audio_stream:
    while True:
        output_packet = output_audio_stream.encode(None)
        if output_packet:
            output.mux(output_packet)
        else:
            break

"""

output_file.close()

print('Done!')

#!/Users/jonathan/dev/GIT/github/ffplayout-engine/venv/bin/python3

import os
import time
import av

dir_path = os.path.dirname(os.path.realpath(__file__))

output = av.open('remux.mkv', 'w')

out_stream_v = output.add_stream('libx264', 25)
out_stream_a = output.add_stream('aac')
out_stream_v.width = 1024
out_stream_v.height = 576
out_stream_v.options = {'preset': 'faster', 'crf': '24'}
out_stream_a.options = {}


list = [
    'test.mp4'
]

current_frame = 0
last_frame = None

for clip in list:
    input_ = av.open(os.path.join(dir_path, 'test_clips', clip))

    in_stream_v = input_.streams.video[0]
    in_stream_a = input_.streams.audio[0]

    start = time.time()

    for packet in input_.demux(in_stream_v, in_stream_a):
        if packet.dts is None:
            continue

        type = packet.stream.type

        for frame in packet.decode():
            if type == 'video':
                packet = out_stream_v.encode(frame)
            elif type == 'audio':
                packet = out_stream_a.encode(frame)

            current_frame = frame.time

            if last_frame:
                _timer = current_frame - last_frame
                time.sleep(_timer)

            last_frame = current_frame

            output.mux(packet)

end = time.time()

print(end - start)

output.close()

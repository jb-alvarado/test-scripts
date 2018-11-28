#!/Users/jonathan/dev/GIT/github/ffplayout-engine/venv/bin/python3

import os

import av

dir_path = os.path.dirname(os.path.realpath(__file__))

output = av.open('concat.mkv', 'w')

out_stream_v = output.add_stream('libx264', 25)
out_stream_a = output.add_stream('aac')
out_stream_v.width = 1024
out_stream_v.height = 576
out_stream_v.options = {'preset': 'faster', 'crf': '24'}
out_stream_a.options = {'b': '128k'}


list = [
    'test.mp4',
    'test.mp4',
]

new_video_pts = 0
new_audio_pts = 0

for clip in list:
    input_ = av.open(os.path.join(dir_path, 'test_clips', clip))
    print(input_)

    resampler = av.AudioResampler(
        format=av.AudioFormat('s16'),
        layout=2,
        rate=44100,
    )

    in_stream_v = input_.streams.video[0]
    in_stream_a = input_.streams.audio[0]

    for packet in input_.demux(in_stream_v, in_stream_a):
        if packet.dts is None:
            continue

        type = packet.stream.type

        for frame in packet.decode():
            if type == 'video':
                # print('type: ', frame.type)
                frame.pts = new_video_pts
                new_v_frame = frame.reformat(1024, 576, 'yuv420p')
                packet = out_stream_v.encode(new_v_frame)
                new_video_pts += 512

            elif type == 'audio':
                # new_a_frame = resampler.resample(frame)
                frame.pts = new_audio_pts
                packet = out_stream_a.encode(frame)
                new_audio_pts += 1024

            output.mux(packet)

output.close()

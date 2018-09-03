import argparse
import av
import av.filter

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("inputpath")
    args = parser.parse_args()

    icntnr = av.open(args.inputpath)
    ocntnr = av.open(args.inputpath + ".out.mp4", "w")

    ivstrm = next(s for s in icntnr.streams if s.type == 'video')
    iastrm = next(s for s in icntnr.streams if s.type == 'audio')
    ostrms = {
        "audio": ocntnr.add_stream(codec_name="aac", rate=iastrm.average_rate),
        "video": ocntnr.add_stream(codec_name="h264", rate=ivstrm.average_rate),
        }

    graph = av.filter.Graph()
    # you can enumerate available filters with av.filter.filters_available.
    #print(av.filter.filters_available)
    #

    fchain = []
    fchain.append(graph.add_buffer(template=ivstrm))
    fchain.append(graph.add("vflip"))
    fchain[-2].link_to(fchain[-1])
    fchain.append(graph.add("hflip"))
    fchain[-2].link_to(fchain[-1])
    fchain.append(graph.add("dilation"))
    fchain[-2].link_to(fchain[-1])
    fchain.append(graph.add("buffersink"))  # graph must end with buffersink...?
    fchain[-2].link_to(fchain[-1])

    for packet in icntnr.demux():
        for ifr in packet.decode():
            typ = packet.stream.type
            if typ == 'audio':
                ifr.pts = None
                for p in ostrms[typ].encode(ifr):
                    ocntnr.mux(p)
            else:
                fchain[0].push(ifr)
                ofr = fchain[-1].pull()
                ofr.pts = None
                for p in ostrms[typ].encode(ofr):
                    ocntnr.mux(p)

    ocntnr.close()

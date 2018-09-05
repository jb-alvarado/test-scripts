#!/usr/bin/env python3

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

import re
from ast import literal_eval
from os import path
import xml.etree.ElementTree as ET

import logwriter
import utils
from settings import playlist


# read values from xml playlist
def iter_src_commands():
    last_time = None
    last_mod_time = 0.0
    source = [None]
    last = False
    list_date = utils.get_date(True)
    dummy_len = 60

    while True:
        year, month, day = re.split('-', list_date)
        xml_path = path.join(playlist.path, year, month, list_date + '.xml')

        if utils.check_file_exist(xml_path):
            # check last modification from playlist
            mod_time = path.getmtime(xml_path)
            if mod_time > last_mod_time:
                xml_file = open(xml_path, "r")
                xml_root = ET.parse(xml_file).getroot()
                clip_nodes = xml_root.findall('body/video')
                xml_file.close()
                last_mod_time = mod_time
                logwriter.logger.info('open: ' + xml_path)
                utils.validate_thread(clip_nodes)
                last_node = clip_nodes[-1]

            # when last clip is None or a dummy,
            # we have to jump to the right place in the playlist
            first, last_time = utils.check_last_item(source, last_time, last)

            # loop through all clips in playlist
            for clip_node in clip_nodes:
                if playlist.map_ext:
                    _ext = literal_eval(playlist.map_ext)
                    node_src = clip_node.get('src').replace(
                        _ext[0], _ext[1])
                else:
                    node_src = clip_node.get('src')

                src = node_src
                begin = utils.is_float(
                    clip_node.get('begin'), last_time, True)
                duration = utils.is_float(
                    clip_node.get('dur'), dummy_len, True)
                seek = utils.is_float(clip_node.get('in'), 0, True)
                out = utils.is_float(clip_node.get('out'), dummy_len, True)

                # first time we end up here
                if first and last_time < begin + duration:
                    # calculate seek time
                    seek = last_time - begin + seek
                    source, time_left = utils.gen_input(
                        src, begin, duration, seek, out, False
                    )

                    first = False
                    last_time = begin
                    break
                elif last_time < begin:
                    if clip_node == last_node:
                        last = True
                    else:
                        last = False

                    source, time_left = utils.gen_input(
                        src, begin, duration, seek, out, last
                    )

                    if time_left is None:
                        # normal behavior
                        last_time = begin
                    elif time_left > 0.0:
                        # when playlist is finish and we have time left
                        last_time = begin
                        list_date = utils.get_date(False)
                        dummy_len = time_left

                    else:
                        # when there is no time left and we are in time,
                        # set right values for new playlist
                        list_date = utils.get_date(False)
                        last_time = float(playlist.start * 3600 - 5)
                        last_mod_time = 0.0

                    break
            else:
                # when playlist exist but is empty, or not long enough,
                # generate dummy and send log
                source, last_time, first = utils.exeption(
                    'Playlist is not valid!', dummy_len, xml_path, last
                )

                begin = utils.get_time('full_sec')
                last = False
                dummy_len = 60
                last_mod_time = 0.0

        else:
            # when we have no playlist for the current day,
            # then we generate a black clip
            # and calculate the seek in time, for when the playlist comes back
            source, last_time, first = utils.exeption(
                'Playlist not exist:', dummy_len, xml_path, last
            )

            begin = utils.get_time('full_sec')
            last = False
            dummy_len = 60
            last_mod_time = 0.0

        if source is not None:
            yield source, begin


if __name__ == '__main__':
    from time import sleep

    for source, begin in iter_src_commands():
        print(begin, source)
        sleep(5)

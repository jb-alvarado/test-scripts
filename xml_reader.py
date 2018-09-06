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
from os import path
import xml.etree.ElementTree as ET

import utils
from logger import logger
from settings import playlist


# read values from xml playlist
class GetSourceIter:
    def __init__(self):
        self.last_time = utils.get_time('full_sec')
        self.last_mod_time = 0.0
        self.clip_nodes = None
        self.first = True
        self.last = False
        self.list_date = utils.get_date(True)
        self.dummy_len = 60

        if 0 <= self.last_time < playlist.start * 3600:
            self.last_time += 86400

    def get_playlist(self, xml_path):
        # check last modification from playlist
        mod_time = path.getmtime(xml_path)
        if mod_time > self.last_mod_time:
            # open and parse xml playlist
            xml_file = open(xml_path, "r")
            xml_root = ET.parse(xml_file).getroot()
            self.clip_nodes = xml_root.findall('body/video')
            xml_file.close()
            # update modification time
            self.last_mod_time = mod_time
            logger.info('open: ' + xml_path)
            # send nodes to a validation thread to check
            # if all values are correct
            utils.validate_thread(self.clip_nodes)

        return self.clip_nodes

    def __iter__(self):
        return self

    def __next__(self):
        while True:
            # get playlist of this day
            year, month, day = re.split('-', self.list_date)
            xml_path = path.join(
                playlist.path, year, month, self.list_date + '.xml')

            if utils.check_file_exist(xml_path):
                clip_nodes = self.get_playlist(xml_path)

                # loop through all clips in playlist
                for node in clip_nodes:
                    # get all necessary values
                    # is_float: check if variable is filled,
                    # when not replace it with a given value
                    source = utils.get_source(node.get('src'))
                    begin = utils.is_float(
                        node.get('begin'), self.last_time, True)
                    dur = utils.is_float(node.get('dur'), self.dummy_len, True)
                    seek = utils.is_float(node.get('in'), 0, True)
                    out = utils.is_float(node.get('out'), self.dummy_len, True)

                    # first time we end up here
                    if self.first and self.last_time < begin + out - seek:
                        # calculate seek time
                        seek = self.last_time - begin + seek

                        self.first = False
                        self.last_time = begin
                        break

                    elif self.last_time < begin:
                        seek = 0
                        break

            return source, begin, dur, seek, out


if __name__ == '__main__':
    from time import sleep

    for source, begin, dur, seek, out in GetSourceIter():
        print(begin, dur, seek, out, source)
        sleep(3)

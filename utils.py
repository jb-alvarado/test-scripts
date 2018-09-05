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

import smtplib
from ast import literal_eval
from datetime import datetime, date, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from os import path
from threading import Thread
from time import sleep

from logwriter import logger
import settings


# get time
def get_time(time_format):
    t = datetime.today() + timedelta(seconds=settings.playlist.shift)
    if time_format == 'hour':
        return t.hour
    elif time_format == 'full_sec':
        sec = float(t.hour * 3600 + t.minute * 60 + t.second)
        micro = float(t.microsecond) / 1000000
        return sec + micro
    else:
        return t.strftime("%H:%M:%S")


# get date
def get_date(seek_day):
    d = date.today() + timedelta(seconds=settings.playlist.shift)
    if get_time('hour') < settings.playlist.start and seek_day:
        yesterday = d - timedelta(1)
        return yesterday.strftime('%Y-%m-%d')
    else:
        return d.strftime('%Y-%m-%d')


# send error messages to email addresses
def mail_or_log(message, time, path):
    if settings.mail.recip:
        msg = MIMEMultipart()
        msg['From'] = settings.mail.s_addr
        msg['To'] = settings.mail.recip
        msg['Subject'] = "Playout Error"
        msg.attach(MIMEText('{} {}\n{}'.format(time, message, path), 'plain'))
        text = msg.as_string()

        server = smtplib.SMTP(settings.mail.server, int(settings.mail.port))
        server.starttls()
        server.login(settings.mail.s_addr, settings.mail.s_pass)
        server.sendmail(settings.mail.s_addr, settings.mail.recip, text)
        server.quit()
    else:
        logger.error('{} {}'.format(message, path))


# check if processes a well
def check_process(watch_proc, terminate_proc):
    while True:
        sleep(4)
        if watch_proc.poll() is not None:
            terminate_proc.terminate()
            break


# check if path exist,
# when not send email and generate blackclip
def check_file_exist(in_file):
    if path.exists(in_file):
        return True
    else:
        return False


# seek in clip and cut the end
def seek_in_cut_end(in_file, duration, seek, out):
    if seek > 0.0:
        inpoint = ['-ss', str(seek)]
        fade_in_vid = 'fade=in:st=0:d=0.5'
        fade_in_aud = 'afade=in:st=0:d=0.5'
    else:
        inpoint = []
        fade_in_vid = 'null'
        fade_in_aud = 'anull'

    if out < duration:
        fade_out_time = out - seek - 1.0
        cut_end = ['-t', str(out - seek)]
        fade_out_vid = 'fade=out:st=' + str(fade_out_time) + ':d=1.0'
        fade_out_aud = 'afade=out:st=' + str(fade_out_time) + ':d=1.0'
    else:
        cut_end = []
        fade_out_vid = 'null'
        fade_out_aud = 'anull'

        return inpoint + ['-i', in_file] + cut_end + [
            '-vf', fade_in_vid + ',' + fade_out_vid,
            '-af', fade_in_aud + ',' + fade_out_aud
        ]


# when source path exist, generate input with seek and out time
# when path not exist, generate dummy clip
def src_or_dummy(src, duration, seek, out, dummy_len=None):
    if check_file_exist(src):
        if seek > 0.0 or out < duration:
            return seek_in_cut_end(src, duration, seek, out)
        else:
            return src
    else:
        mail_or_log(
            'Clip not exist:', get_time(None),
            src
        )
        return None


# prepare input clip
# check begin and length from clip
# return clip only if we are in 24 hours time range
def gen_input(src, begin, dur, seek, out, last):
    start = float(settings.playlist.start * 3600)
    day_in_sec = 86400.0
    ref_time = day_in_sec + start
    time = get_time('full_sec')

    if 0 <= time < start:
        time += day_in_sec

    # calculate time difference to see if we are sync
    time_diff = out - seek + time

    if (time_diff <= ref_time or begin < day_in_sec) and not last:
        # when we are in the 24 houre range, get the clip
        return src_or_dummy(src, dur, seek, out, 20), None
    elif time_diff < ref_time and last:
        # when last clip is passed and we still have too much time left
        # check if duration is larger then out - seek
        time_diff = dur + time
        new_len = dur - (time_diff - ref_time)
        logger.info('we are under time, length is: {}'.format(new_len))

        if time_diff >= ref_time:
            if src == settings.playlist.filler:
                # when filler is something like a clock,
                # is better to start the clip later and to play until end
                src_cmd = src_or_dummy(src, dur, dur - new_len, dur)
            else:
                src_cmd = src_or_dummy(src, dur, 0, new_len)
        else:
            src_cmd = src_or_dummy(src, dur, 0, dur)

            mail_or_log(
                'playlist is not long enough:', get_time(None),
                str(new_len) + ' seconds needed.'
            )

        return src_cmd, new_len - dur

    elif time_diff > ref_time:
        new_len = out - seek - (time_diff - ref_time)
        # when we over the 24 hours range, trim clip
        logger.info('we are over time, new_len is: {}'.format(new_len))

        if new_len > 5.0:
            if src == settings.playlist.filler:
                src_cmd = src_or_dummy(src, dur, out - new_len, out)
            else:
                src_cmd = src_or_dummy(src, dur, seek, new_len)
        elif new_len > 1.0:
            src_cmd = None
        else:
            src_cmd = None

        return src_cmd, 0.0


# test if value is float
def is_float(value, text, convert):
    try:
        float(value)
        if convert:
            return float(value)
        else:
            return ''
    except ValueError:
        return text


# check last item, when it is None or a dummy clip,
# set true and seek in playlist
def check_last_item(src_cmd, last_time, last):
    if src_cmd is None and not last:
        first = True
        last_time = get_time('full_sec')
        if 0 <= last_time < settings.playlist.start * 3600:
            last_time += 86400

    elif 'lavfi' in src_cmd and not last:
        first = True
        last_time = get_time('full_sec')
        if 0 <= last_time < settings.playlist.start * 3600:
            last_time += 86400
    else:
        first = False

    return first, last_time


# validate xml values in new Thread
# and test if file path exist
def validate_thread(clip_nodes):
    def check_xml(xml_nodes):
        error = ''

        # check if all values are valid
        for xml_node in xml_nodes:
            if settings.playlist.map_ext:
                _ext = literal_eval(settings.playlist.map_ext)
                node_src = xml_node.get('src').replace(
                    _ext[0], _ext[1])
            else:
                node_src = xml_node.get('src')

            if check_file_exist(node_src):
                a = ''
            else:
                a = 'File not exist! '

            b = is_float(xml_node.get('begin'), 'No Start Time! ', False)
            c = is_float(xml_node.get('dur'), 'No Duration! ', False)
            d = is_float(xml_node.get('in'), 'No In Value! ', False)
            e = is_float(xml_node.get('out'), 'No Out Value! ', False)

            line = a + b + c + d + e
            if line:
                error += line + 'In line: ' + str(xml_node.attrib) + '\n'

        if error:
            mail_or_log(
                'Validation error, check xml playlist, values are missing:\n',
                get_time(None), error
            )

        # check if playlist is long enough
        last_begin = is_float(clip_nodes[-1].get('begin'), 0, True)
        last_duration = is_float(clip_nodes[-1].get('dur'), 0, True)
        start = float(settings.playlist.start * 3600)
        total_play_time = last_begin + last_duration - start

        if total_play_time < 86395.0:
            mail_or_log(
                'xml playlist is not long enough!',
                get_time(None), "total play time is: " + str(total_play_time)
            )

    validate = Thread(name='check_xml', target=check_xml, args=(clip_nodes,))
    validate.daemon = True
    validate.start()


# exaption gets called, when there is no playlist,
# or the playlist is not long enough
def exeption(message, dummy_len, path, last):
    src_cmd = None

    if last:
        last_time = float(settings.playlist.start * 3600 - 5)
        first = False
    else:
        last_time = (
            get_time('full_sec') + dummy_len
        )

        if 0 <= last_time < settings.playlist.start * 3600:
            last_time += 86400

        first = True

    mail_or_log(message, get_time(None), path)

    return src_cmd, last_time, first

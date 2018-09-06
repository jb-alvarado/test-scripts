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

from logger import logger
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


# check if path exist,
# when not send email and generate blackclip
def check_file_exist(in_file):
    if path.exists(in_file):
        return True
    else:
        return False


# replace extension
def map_extension(src):
    if settings.playlist.map_ext:
        old_ext, new_ext = literal_eval(settings.playlist.map_ext)
        return src.replace(old_ext, new_ext)
    else:
        return src


# get input clip and when is active, rename the extension
def get_source(source):
    if check_file_exist(source):
        return map_extension(source)
    else:
        return None


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

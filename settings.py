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

import configparser
from ast import literal_eval
from os import path
from types import SimpleNamespace

# read config
cfg = configparser.ConfigParser()
if path.exists("/etc/ffplayout/ffplayout-engine.conf"):
    cfg.read("/etc/ffplayout/ffplayout-engine.conf")
else:
    cfg.read("ffplayout-engine.conf")

mail = SimpleNamespace(
    server=cfg.get('MAIL', 'smpt_server'),
    port=cfg.getint('MAIL', 'smpt_port'),
    s_addr=cfg.get('MAIL', 'sender_addr'),
    s_pass=cfg.get('MAIL', 'sender_pass'),
    recip=cfg.get('MAIL', 'recipient')
)

log = SimpleNamespace(
    path=cfg.get('LOGGING', 'log_file'),
    level=cfg.get('LOGGING', 'log_level')
)

pre_proc = SimpleNamespace(
    w=cfg.getint('PRE_PROCESS', 'width'),
    h=cfg.getint('PRE_PROCESS', 'height'),
    aspect=cfg.getfloat(
        'PRE_PROCESS', 'width') / cfg.getfloat('PRE_PROCESS', 'height'),
    fps=cfg.getint('PRE_PROCESS', 'fps'),
    a_sample=cfg.getint('PRE_PROCESS', 'a_sample')
)

playlist = SimpleNamespace(
    path=cfg.get('PLAYLIST', 'playlist_path'),
    start=cfg.getint('PLAYLIST', 'day_start'),
    filler=cfg.get('PLAYLIST', 'filler_clip'),
    shift=cfg.getint('PLAYLIST', 'time_shift'),
    map_ext=cfg.get('PLAYLIST', 'map_extension')
)

playout = SimpleNamespace(
    name=cfg.get('OUT', 'service_name'),
    provider=cfg.get('OUT', 'service_provider'),
    logo=cfg.get('OUT', 'logo'),
    logo_filter=cfg.get('OUT', 'logo_o'),
    out_addr=cfg.get('OUT', 'out_addr'),
    post_comp_video=literal_eval(cfg.get('OUT', 'post_comp_video')),
    post_comp_audio=literal_eval(cfg.get('OUT', 'post_comp_audio')),
    post_comp_extra=literal_eval(cfg.get('OUT', 'post_comp_extra')),
)

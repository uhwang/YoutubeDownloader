'''
    reutil.py

    Author: Uisang Hwang
    
'''

import re
import ydlconst

_check_time      = re.compile ( '([0-9]{2}):([0-9]{2}):([0-9]{2}).([0-9]{2})')
_find_time       = _check_time

_find_format     = re.compile('\w+', re.MULTILINE )
_find_percent    = re.compile('\d+.\d+\%', re.MULTILINE )
_find_digit      = re.compile('\d+')
_find_bitrate    = re.compile('\d+[kK]')
_find_error      = re.compile("%s|%s"%(ydlconst._ydl_const_warning, \
                                       ydlconst._ydl_const_error), re.MULTILINE)
_find_int        = _find_digit                                       

# https://stackoverflow.com/questions/28735459/how-to-validate-youtube-url-in-client-side-in-text-box
_valid_youtube_url = re.compile("^(?:https?:\/\/)?(?:m\.|www\.)?"\
                                "(?:youtu\.be\/|youtube\.com\/"\
                                "(?:embed\/|v\/|playlist\?list="\
                                "|watch\?v=|watch\?.+&v=))((\w|-){11})(?:\S+)?$")

# 936.10KiB  1.07MiB  18.07MiB  GiB
_find_size       = re.compile("\d*\.?\d*[KMG]iB")
_find_file_size  = lambda x: _find_size.search(x)
_find_ydl_error  = lambda x: x.strip() if x.find(ydlconst._ydl_const_error) >= 0 else None
_find_ydl_warning= lambda x: x.strip() if x.find(ydlconst._ydl_const_warning) >= 0 else None
_file_exist      = lambda x: True if x.find(ydlconst._ydl_const_exist) >= 0 else False
_find_filename   = lambda x: x.split(ydlconst._ydl_const_filename)[1] if x.find(ydlconst._ydl_const_filename) >= 0 else None
_exception_msg   = lambda e: "{0} : {1}".format(type(e).__name__, str(e))
_string_to_bool  = lambda x: True if x.lower() == "true" else False
_yesno_to_bool   = lambda x: True if x.lower() == "yes" else False

_find_vlist_range = re.compile("(\d+)-(\d+)")
_find_video_sequence = re.compile("(\d+) of (\d+)")

_url_is_vimeo = lambda x: True if x.lower().find("vimeo") > -1 else False
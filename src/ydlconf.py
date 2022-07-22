'''
    ydlconf.py
    
    Youtube Downloader Config

    Author: Uisang Hwang
    
'''
import json
import util
import reutil
import msg

_ydl_config_file = "ydl.conf"

_config = None

def dump_config():
    return "filename_pattern         : %s\n"\
           "Fetch Tmeout             : %s\n"\
           "Single Timeout           : %s\n"\
           "Sequential Timeout       : %s\n"\
           "Concurrent Timeout       : %s\n"\
           "Encoding                 : %s\n"\
           "Single Timer Interval    : %s\n"\
           "Sequential Timer Interval: %s\n"\
           "Concurrent Timer Interval: %s\n"\
           "Limit Max Process        : %s\n"\
           "Max Process              : %s\n"\
           "Tracker Height           : %s\n"\
           %(
                _config["youtube-dl"]["filename_pattern"],
                _config["youtube-dl"]["fetch_timeout"],
                _config["youtube-dl"]["single_timeout"],
                _config["youtube-dl"]["sequential_timeout"],
                _config["youtube-dl"]["concurrent_timeout"],
                _config["youtube-dl"]["encoding"],
                _config["timer"]["single_timer_interval"],
                _config["timer"]["sequential_timer_interval"],
                _config["timer"]["concurrent_timer_interval"],
                _config["concurrent"]["limit_max_process"],
                _config["concurrent"]["max_process"],
                _config["concurrent"]["tracker_height"]
            )
    
def get_filename_pattern():
    return _config["youtube-dl"]["filename_pattern"]
    
def get_fetch_timeout_duration(): 
    return _config["youtube-dl"]["fetch_timeout"].split(' ')[0]
    
def get_single_download_timeout_duration(): 
    return _config["youtube-dl"]["single_timeout"].split(' ')[0]
    
def get_sequential_download_timeout_duration(): 
    return _config["youtube-dl"]["sequential_timeout"].split(' ')[0]

def get_concurrent_download_timeout_duration(): 
    return _config["youtube-dl"]["concurrent_timeout"].split(' ')[0]
    
def get_encoding(): 
    return _config["youtube-dl"]["encoding"]
    
def get_single_download_timer_interval(): 
    return int(_config["timer"]["single_timer_interval"].split(' ')[0])
    
def get_sequential_download_timer_interval(): 
    return int(_config["timer"]["sequential_timer_interval"].split(' ')[0])
    
def get_concurrent_download_timer_interval(): 
    return int(_config["timer"]["concurrent_timer_interval"].split(' ')[0])
    
def get_limit_max_process(): 
    return reutil._string_to_bool(_config["concurrent"]["limit_max_process"])
    
def get_max_process(): 
    return int(_config["concurrent"]["max_process"])

def get_tacker_height(): 
    return int(_config["concurrent"]["tracker_height"])
    
def set_default_config():
    global _config
    
    _config["youtube-dl"] = {
            "filename_pattername": "%(title)s-%(id)s.%(ext)s",
            "fetch_timeout"      : "30 sec",
            "single_timeout"     : "60 sec",
            "sequential_timeout" : "60 sec",
            "encoding"           : "cp949"
        }
        
    _config["timer"] = {
            "single_timer_interval"      : "100 ms",
            "sequential_timer_interval"  : "100 ms",
            "concurrent_timer_interval"  : "50 ms"
        }
        
    _config["concurrent"] = {
            "limit_max_process" : "True",
            "max_process"       : "10",
            "tracker_height"    : "300"
        }
    
def save_config():
    try:
        with open(_ydl_config_file, 'w') as f:
            json.dump(_config, f, ensure_ascii=False, indent=4)
    except Exception as e:    
        msg.message_box(str(e), msg.message_error)
        
def load_config():
    global _config
 
    try: 
        with open(_ydl_config_file, "rt") as fp:
            _config = json.load(fp)
    except Exception as e:
        msg.message_box(str(e), msg.message_error)
        set_default_config()
     
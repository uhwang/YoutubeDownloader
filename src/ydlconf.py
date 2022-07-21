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

class YdlConfig():
    # youtube-dl
    _fetch_timeout_duration                = 30 # sec
    _single_download_timeout_duration      = 60 # sec
    _sequential_download_timeout_duration  = 60 # sec
    
    # timer
    _single_download_timer_interval          = 100 # milisec
    _sequential_download_timer_interval      = 100 # ms
    _concurrent_download_timer_interval      = 100 # ms
    
    # concurrent
    _limit_max_process_count = True
    _max_process_count       = 10
    _tracker_max_height      = 200

    def __init__(self):
        pass
        
    def __str__(self):
        return "Fetch Tmeout             : %d ms\n"\
               "Single Timeout           : %d ms\n"\
               "Sequential Timeout       : %d ms\n"\
               "Single Timer Interval    : %d ms\n"\
               "Sequential Timer Interval: %d ms\n"\
               "Concurrent Timer Interval: %d ms\n"\
               "Limit Max Process Count  : %s\n"\
               "Max Process Count        : %d\n"\
               "Tracker Max Height       : %d\n"\
               %(
                    YdlConfig._fetch_timeout_duration,
                    YdlConfig._single_download_timeout_duration,
                    YdlConfig._sequential_download_timeout_duration,
                    YdlConfig._single_download_timer_interval,
                    YdlConfig._sequential_download_timer_interval,
                    YdlConfig._concurrent_download_timer_interval,
                    YdlConfig._limit_max_process_count,
                    YdlConfig._max_process_count,
                    YdlConfig._tracker_max_height
               )
    
_config_var = YdlConfig()

def dump_config():
    return str(_config_var)
    
def get_fetch_timeout_duration(): 
    return YdlConfig._fetch_timeout_duration
    
def get_single_download_timeout_duration(): 
    return YdlConfig._single_download_timeout_duration
    
def get_sequential_download_timeout_duration(): 
    return YdlConfig._sequential_download_timeout_duration
    
def get_single_download_timer_interval(): 
    return YdlConfig._single_download_timer_interval
    
def get_sequential_download__timer_interval(): 
    return YdlConfig._sequential_download__timer_interval    
    
def get_concurrent_download_timer_interval(): 
    return YdlConfig._concurrent_download_timer_interval
    
def get_limit_max_process_count(): 
    return YdlConfig._limit_max_process_count
    
def get_max_process_count(): 
    return YdlConfig._max_process_count

def get_tacker_max_height(): 
    return YdlConfig._tracker_max_height
    
def load_config():
    global _config
    
    try: 
        with open(_ydl_config_file, "rt") as fp:
            _config = json.load(fp)
    except Exception as e:
        msg.message_box(str(e), msg.message_error)
        return None

    ydl   = _config["youtube-dl"]
    timer = _config["timer"]
    concur= _config["concurrent"]
   
    YdlConfig._fetch_timeout_duration                 = int(reutil._find_int.search(ydl["fetch_timeout_duration"])[0])
    YdlConfig._single_download_timeout_duration       = int(reutil._find_int.search(ydl["single_download_timeout_duration"])[0])
    YdlConfig._sequential_download_timeout_duration   = int(reutil._find_int.search(ydl["sequential_download_timeout_duration"])[0])
    YdlConfig._single_download_timer_interval         = int(reutil._find_int.search(timer["single_download_timer_interval"])[0])
    YdlConfig._sequential_download__timer_interval    = int(reutil._find_int.search(timer["sequential_download__timer_interval"])[0])
    YdlConfig._concurrent_download_timer_interval     = int(reutil._find_int.search(timer["concurrent_download_timer_interval"])[0])
    YdlConfig._limit_max_process_count                = reutil._string_to_bool(concur["limit_max_process_count"])
    YdlConfig._max_process_count                      = int(reutil._find_int.search(concur["max_process_count"])[0])
    YdlConfig._tracker_max_height                     = int(reutil._find_int.search(concur["tracker_max_height"])[0])
    
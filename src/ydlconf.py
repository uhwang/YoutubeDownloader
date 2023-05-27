'''
    ydlconf.py
    
    Youtube Downloader Config
    
    02/23/22 Change code for yt-dlp.exe

    Author: Uisang Hwang
    
'''
import os
import json
import util
import reutil
import msg
import ydlconst
from pathlib import Path, PurePath

_ydl_config_file = "ydl.conf"

_config = {}
_config_dict_keys = ["ydl_exec", "timer", "concurrent", "download"]
def _get_config_key_exec(): return _config_dict_keys[0]
def _get_config_key_timer(): return _config_dict_keys[1]
def _get_config_key_concurrent(): return _config_dict_keys[2]
def _get_config_key_download(): return _config_dict_keys[3]

def dump_config():
    return "Output : %s\n"\
           "Executable          : %s\n"\
           "Fetch Tmeout        : %s\n"\
           "Single Timeout      : %s\n"\
           "Sequential Timeout  : %s\n"\
           "Concurrent Timeout  : %s\n"\
           "Encoding            : %s\n"\
           "Interval Single     : %s\n"\
           "Interval Sequential : %s\n"\
           "Interval Concurrent : %s\n"\
           "Limit Max Process   : %s\n"\
           "Max Process         : %s\n"\
           "Tracker Height      : %s\n"\
           "Download Path       : %s\n"\
           %(
                _config[_get_config_key_exec()]["output"],
                _config[_get_config_key_exec()]["executable"],
                _config[_get_config_key_exec()]["fetch_timeout"],
                _config[_get_config_key_exec()]["single_timeout"],
                _config[_get_config_key_exec()]["sequential_timeout"],
                _config[_get_config_key_exec()]["concurrent_timeout"],
                _config[_get_config_key_exec()]["encoding"],
                _config[_get_config_key_timer()]["interval_single"],
                _config[_get_config_key_timer()]["interval_sequential"],
                _config[_get_config_key_timer()]["interval_concurrent"],
                _config[_get_config_key_concurrent()]["limit_max_process"],
                _config[_get_config_key_concurrent()]["max_process"],
                _config[_get_config_key_concurrent()]["tracker_height"],
                _config[_get_config_key_download()]["path"]
            )
    
def get_filename_pattern():
    return _config[_get_config_key_exec()]["output"]

def get_executable_name():
    return _config[_get_config_key_exec()]["executable"]
    
def get_fetch_timeout_duration(): 
    return _config[_get_config_key_exec()]["fetch_timeout"].split(' ')[0]
    
def get_single_download_timeout_duration(): 
    return _config[_get_config_key_exec()]["single_timeout"].split(' ')[0]
    
def get_sequential_download_timeout_duration(): 
    return _config[_get_config_key_exec()]["sequential_timeout"].split(' ')[0]

def get_concurrent_download_timeout_duration(): 
    return _config[_get_config_key_exec()]["concurrent_timeout"].split(' ')[0]
    
def get_encoding(): 
    return _config[_get_config_key_exec()]["encoding"]
    
def get_single_download_timer_interval(): 
    return int(_config[_get_config_key_timer()]["interval_single"].split(' ')[0])
    
def get_sequential_download_timer_interval(): 
    return int(_config[_get_config_key_timer()]["interval_sequential"].split(' ')[0])
    
def get_concurrent_download_timer_interval(): 
    return int(_config[_get_config_key_timer()]["interval_concurrent"].split(' ')[0])
    
def get_limit_max_process(): 
    return reutil._yesno_to_bool(_config[_get_config_key_concurrent()]["limit_max_process"])
    
def get_max_process(): 
    return int(_config[_get_config_key_concurrent()]["max_process"])

def get_tacker_height(): 
    return int(_config[_get_config_key_concurrent()]["tracker_height"])
    
def get_download_path(): 
    return _config[_get_config_key_download()]["path"]

def set_download_path(path): 
    _config[_get_config_key_download()]["path"] = path
    
def check_download_folder(ydl_msg):
    path = _config[_get_config_key_download()]["path"]
    
    p = Path(path)
    if p.exists() == False:
        download_path = str(PurePath(Path.cwd()).joinpath("download"))
        ydl_msg.appendPlainText("... Error: current path not exist\n"\
                                "... Creating download folder\n==>%s\n"%download_path)
        try:
            Path.mkdir(download_path)
        except Exception as e:
            ydl_msg.appendPlainText("... Error: can't create folder\nSet download folder manually(click button)")
       
        _config[_get_config_key_download()]["path"] = download_path
        
def set_default_config(ydl_msg):
    global _config
    
    _config[_get_config_key_exec()] = {
            "output"             : "%(title)s [%(id)s].%(ext)s",
            "executable"         : ydlconst._ydl_executable_name,
            "fetch_timeout"      : "30 sec",
            "single_timeout"     : "60 sec",
            "sequential_timeout" : "60 sec",
            "concurrent_timeout" : "60 sec",
            "encoding"           : "cp949"
        }
        
    _config[_get_config_key_timer()] = {
            "interval_single"      : "100 ms",
            "interval_sequential"  : "100 ms",
            "interval_concurrent"  : "50 ms"
        }
        
    _config[_get_config_key_concurrent()] = {
            "limit_max_process" : "yes",
            "max_process"       : "10",
            "tracker_height"    : "300"
        }

    _config[_get_config_key_download()] = {
            "path" : "download"
        }
    check_download_folder(ydl_msg)
    
def save_config(ydl_exec_path):
    global _config
    
    try:
        exe_path = os.path.join(ydl_exec_path,_ydl_config_file)
        with open(exe_path, 'w') as fp:
            json.dump(_config, fp, ensure_ascii=False, indent=4)
    except Exception as e:    
        msg.message_box(str(e), msg.message_error)
        
def load_config(ydl_msg):
    global _config
 
    ydl_msg.appendPlainText("... Loading config")
    try: 
        with open(_ydl_config_file, "rt") as fp:
            _config = json.load(fp)
    except Exception as e:
        msg.message_box(str(e), msg.message_error)
        ydl_msg.appendPlainText("... No config found: load default value")
        set_default_config(ydl_msg)
        
    check_download_folder(ydl_msg)

'''
    funs.py
    
    Author: Uisang Hwang
    
'''

import ydlconst

def get_best_codec_name(): return ydlconst._ydl_video_codec[0]
def get_mkv_codec_name(): return ydlconst._ydl_video_codec[5]

def get_sequential_download_text() : return ydlconst._ydl_multiple_download_method[0]
def get_concurrent_download_text() : return ydlconst._ydl_multiple_download_method[1]
def get_current_tab_text(tab) : tab.tabText(tab.currentIndex())

def get_single_tab_text  () : return ydlconst._youtube_tab_text[0]
def get_multiple_tab_text() : return ydlconst._youtube_tab_text[1]
def get_youtubetab_text  () : return ydlconst._youtube_tab_text[3]
def get_messagetab_text  () : return ydlconst._youtube_tab_text[4]
def get_youtubedl_setting_tab_text() : return ydlconst._youtube_tab_text[2]
def get_urllisttab_text() : return ydlconst._youtube_tab_text[5]
def get_encodetab_text() : return ydlconst._encode_tab_text[0]

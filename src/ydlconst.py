'''
    ydlconst.py
    
    Author: Uisang Hwang
    
'''

_ydl_option_timeout_duration= "30" # secs
_ydl_option_socket_timeout  = "--socket-timeout"
_ydl_option_video_list      = "--flat-playlist"
_ydl_option_skip_download   = "--skip-download"
_ydl_option_extract_audio   = "--extract-audio"
_ydl_option_audio_format    = "--audio-format"
_ydl_option_encode_video    = "--recode-video"
_ydl_option_audio_quality   = "--audio-quality"
_ydl_option_output          = "-o"
_ydl_option_output_filename = "%(title)s-%(id)s.%(ext)s"

# --prefer-ffmpeg --postprocessor-arg "-ss 0 -t 5 out.mp4"
_ydl_option_choose_ffmpeg   = "--prefer-ffmpeg"
_ydl_option_ffmpeg_argument = "--postprocessor-args"
#_ydl_option_choose_ffmpeg   = "--external-downloader"
#_ydl_option_ffmpeg_argument = "--external-downloader-args"
_ydl_option_postprocessor   = "ffmpeg"
_ydl_ffmpeg_start_time      = "-ss"
_ydl_ffmpeg_duration        = "-t"
_ydl_ffmpeg_qt_time_mask    = "99:99:99.99;-"
_ydl_ffmpeg_qt_width_mask   = "888888888888"

_ydl_const_warning          = "WARNING"
_ydl_const_error            = "ERROR"
_ydl_const_exist            = "already been downloaded"
_ydl_const_exist_text       = "Already exist"
_ydl_const_filename         = "Destination:"
_ydl_const_finished         = "Finished"

_ydl_download_start = 0x01
_ydl_download_finish = 0x02

_ydl_url_prefix = "https://www.youtube.com/watch?v="

_ydl_format_none   = "N/A"
#_ydl_audio_quality = [ str(x) for x in range(10)]
_ydl_audio_quality = ["0 better", "1", "2", "3", "4", "5 default", "6", "7", "8", "9 worse"]

_ydl_audio_codec = [
    "best", 
    "aac",
    "flac", 
    "mp3", 
    "m4a", 
    "opus", 
    "vorbis", 
    "wav"
]

_ydl_best_audio_codec = _ydl_audio_codec[0]

_ydl_video_codec = [
    "best", # -f 'bestvideo[ext=mp4]+bestaudio[ext=m4a]'
    "mp4",
    "flv",
    "ogg",
    "webm",
    "mkv",
    "avi"
]

_ydl_multiple_download_method = [
    "Sequential",
    "Concurrent"
]

_youtube_tab_text = [ 
    "Single",
    "Multiple",
    "Setting",
    "YouTube",
    "Message",
    "List"
]
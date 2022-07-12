# -*- coding: utf-8 -*-
'''
    Youtube DownLoader w/ PyQt4 & PyQt5

    Author: Uisang Hwang
    
    History
    
    6/02/22     FFMpeg     => self.process.setReadChannel(QtCore.QProcess.StandardError)
                Youtube-dl => self.process.setReadChannel(QtCore.QProcess.StandardOutput) 
                Download a single video from youtube
    06/29/22    Youtube Downloader ver 0.1 
                tested against Windows and Puppy Linux 
                w/ PyQt4 and PyQt5
    07/09/22    Fix table event funcs
    07/09/22    Postprocess w/ FFMpeg cut video/audio
    07/10/22    Exception in case of no internet
    07/11/22    Remove unused code
                
    Note:       Change source code depending on PyQt Version 4/5
                
                ydl.py
                =============================================
                QFileDialog.getOpenFileName returns different value
                PyQt4 : a string 
                PyQt5 : a tuple (file = file[0])
    
                msg.py
                =============================================
                #from PyQt5.QtWidgets import QMessageBox
                from PyQt4.QtGui import QMessageBox
                
                QTableWidget
                =============================================
                setResizeMode (PyQt4) --> setSectionResizeMode s(PyQt5)
                
'''

import re
import os, sys
import subprocess as sp
import datetime
import time
from collections import OrderedDict
from functools import partial
import json

from PyQt5.QtCore import Qt, pyqtSignal, QObject, QProcess, QSize, QBasicTimer
from PyQt5.QtGui import QColor, QIcon, QPixmap, QIntValidator, QFont, QFontMetrics
from PyQt5.QtWidgets import ( QApplication, 
                              QWidget,
                              QStyleFactory, 
                              QDialog,
                              QLabel, 
                              QPushButton, 
                              QLineEdit,
                              QComboBox, 
                              QCheckBox, 
                              QRadioButton, 
                              QTableWidget, 
                              QTableWidgetItem, 
                              QTabWidget,
                              QProgressBar, 
                              QPlainTextEdit, 
                              QGridLayout, 
                              QVBoxLayout, 
                              QHBoxLayout, 
                              QFormLayout, 
                              QButtonGroup,
                              QFileDialog, 
                              QScrollArea,
                              QMessageBox,
                              QHeaderView,
                              QButtonGroup,
                              QGroupBox)


import icon_request_format
import icon_download
import icon_cancel
import icon_edit
import icon_add_row
import icon_folder_open
import icon_youtube
import icon_delete_url
import icon_trash_url
import icon_json
import icon_save
import icon_file_open
import msg

_youtube_tab_text = [ 
    "Single",
    "Multiple",
    "Setting",
    "YouTube",
    "Message"
]

def get_single_tab_text  () : return _youtube_tab_text[0]
def get_multiple_tab_text() : return _youtube_tab_text[1]
def get_youtubetab_text  () : return _youtube_tab_text[3]
def get_messagetab_text  () : return _youtube_tab_text[4]
def get_youtubedl_setting_tab_text() : return _youtube_tab_text[2]

# https://stackoverflow.com/questions/28735459/how-to-validate-youtube-url-in-client-side-in-text-box
_valid_youtube_url = re.compile("^(?:https?:\/\/)?(?:m\.|www\.)?(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|playlist\?list=|watch\?v=|watch\?.+&v=))((\w|-){11})(?:\S+)?$")

_ydl_color_error      = QColor(247,79,83)
_ydl_color_file_exist = QColor(158,248,160)
_ydl_color_finished   = QColor(230,213,89)
_ydl_color_white      = QColor(255,255,255)

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

_ydl_download_start = 0x01
_ydl_download_finish = 0x02

_find_format     = re.compile('\w+', re.MULTILINE )
_find_percent    = re.compile('\d+.\d+\%', re.MULTILINE )
_find_digit      = re.compile('\d+')
_find_bitrate    = re.compile('\d+[kK]')
_find_error      = re.compile("%s|%s"%(_ydl_const_warning, _ydl_const_error), re.MULTILINE)

# 936.10KiB  1.07MiB  18.07MiB  GiB
_find_size       = re.compile("\d*\.?\d*[KMG]iB")
_find_file_size  = lambda x: _find_size.search(x)
_find_ydl_error  = lambda x: x.strip() if x.find(_ydl_const_error) >= 0 else None
_find_ydl_warning= lambda x: x.strip() if x.find(_ydl_const_warning) >= 0 else None
_file_exist      = lambda x: True if x.find(_ydl_const_exist) >= 0 else False
_find_filename   = lambda x: x.split(_ydl_const_filename)[1] if x.find(_ydl_const_filename) >= 0 else None
_exception_msg   = lambda e: "=> {0} : {1}".format(type(e).__name__, str(e))

# from encode.py
_check_time     = re.compile ( '([0-9]{2}):([0-9]{2}):([0-9]{2}).([0-9]{2})')
_find_time      = _check_time

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

def get_best_codec_name(): return _ydl_video_codec[0]
def get_mkv_codec_name(): return _ydl_video_codec[5]

def get_sequential_download_text() : return _ydl_multiple_download_method[0]
def get_concurrent_download_text() : return _ydl_multiple_download_method[1]
def get_current_tab_text(tab) : tab.tabText(tab.currentIndex())

def time_to_sec(t1):
    t2 = _find_time.search(t1)
    sec = 60*(int(t2.group(1))*60+int(t2.group(2)))+int(t2.group(3))+ float(t2.group(4))*.01
    return sec
    
def get_youtube_formats(url, pmsg=None):
    cmd=[ 'youtube-dl',
          _ydl_option_socket_timeout, 
          _ydl_option_timeout_duration,
          '-F', url]
    
    try:
        # https://docs.python.org/3/library/subprocess.html
        # If you wish to capture and combine both streams into one, 
        # use stdout=PIPE and stderr=STDOUT instead of capture_output.
        # youtube-dl emits error and warning to stderr
        proc = sp.Popen(cmd, stdout=sp.PIPE, stderr = sp.STDOUT)
    except Exception as e:
        pmsg.appendPlainText("=> Fetch formats\n=> Error: %s"%str(e))
        msg.message_box(str(e), msg.message_error)
        return None
    	
    output = proc.communicate()[0]
    # http:#stackoverflow.com/questions/606191/convert-bytes-to-a-python-string
    output = output.decode('utf-8')

    # output is a long stream characters
    if _find_error.search(output):
        pmsg.appendPlainText(output)
        msg.message_box("Can't fetch formats\nYou might have network problem\nCheck message", msg.message_error)
        return None

    # output is a list of strings
    output = output.split('\n')
    
    # count commnet lines
    skip_comment = 0
    for o in output:
        o.strip()
        if _find_digit.search(o[0:o.find(' ')]):
            break
        skip_comment += 1
     
    formats = output[skip_comment:]
    del proc
    
    return formats

def get_youtube_format_from_formats(format):

    e = _find_format.findall(format)
    filesize = _find_file_size(format)
    bitrate = _find_bitrate.search(format)

    if len(e) < 1: return None
    
    if format.find('audio') > -1:
        fm = [ e[0], e[1], e[2], bitrate[0], filesize[0], 'audio only']
    else:
        fm = [ e[0], e[1], e[2], bitrate[0], 
               filesize[0] if filesize else "best" if format.find("best")>-1 else "N/A",
               'video only' if format.find('video only')>-1 else "video"]
    return fm
    
def fetch_youtube_format_from_url(url, tbl, pmsg=None):
    
        if not _valid_youtube_url.search(url):
            msg.message_box("Invalid URL", msg.message_error)
            return None

        if url == '':
            return None
        
        formats = get_youtube_formats(url, pmsg)
        if formats == None: return
        
        frm = ["None"]
        
        for i, f in enumerate(formats):
            info = get_youtube_format_from_formats(f)
            if info == None: break
            tbl.insertRow(i)
            tbl.setItem(i, 0, QTableWidgetItem(info[0]))
            tbl.setItem(i, 1, QTableWidgetItem(info[1]))
            tbl.setItem(i, 2, QTableWidgetItem(info[2]))
            tbl.setItem(i, 3, QTableWidgetItem(info[3]))
            tbl.setItem(i, 4, QTableWidgetItem(info[4]))
            tbl.setItem(i, 5, QTableWidgetItem(info[5]))
            frm.append(info[0])
        return frm


class Postprocess:
    def __init__(self):
        self.use_ffmpeg = False
        self.bypass_mkv = False
        self.use_time   = False
        self.t1         = "" # Start => 00:00:00:00 (HH:MM:SS:MS)
        self.t2         = "" # End   => 00:00:00:00 (HH:MM:SS:MS)
        self.filename   = ""
        
    def get_args(self):
        ff_args = list()
        if self.use_time:
            t1_sec = time_to_sec(self.t1)
            t2_sec = time_to_sec(self.t2)
            duration = t2_sec - t1_sec
            ff_args.extend([_ydl_ffmpeg_start_time,
                            "%.2f"%t1_sec,
                            _ydl_ffmpeg_duration,
                            "%.2f"%duration])
        ff_args.append(self.filename)
        return  ' '.join(ff_args)
        
    def __str__(self):
        return  "Use FFMpeg: %s\n"\
                "Bypass MKV: %s\n"\
                "Use Time  : %s\n"\
                "T1        : %s\n"\
                "T2        : %s\n"%(
                self.use_ffmpeg, self.bypass_mkv, self.use_time, 
                self.t1, self.t2)

class PostprocessSingleDownload(Postprocess):
    def __init__(self):
        super(PostprocessSingleDownload, self).__init__()
        
class PostprocessSingleDownloadDlg(QDialog):
    def __init__(self, info):
        super(PostprocessSingleDownloadDlg, self).__init__()
        self.info = info
        self.initUI(info)
        
    def initUI(self, info):
        layout = QFormLayout()
        grid = QGridLayout()
        
        self.bypass_mkv_chk = QCheckBox("Bypass MKV Warning(enforce MP4)")
        self.bypass_mkv_chk.setChecked(info.bypass_mkv)
        
        self.time_group = QGroupBox('Timed Encoding (HH:MM:SS.MS)')
        self.time_group.setFlat(False)
        self.time_group.setCheckable(True)
        self.time_group.clicked.connect(self.timedencoding_state_changed)
        
        time_layout = QHBoxLayout()
        self.timed_encoding_t1 = QLineEdit()
        self.timed_encoding_t2 = QLineEdit()
        self.timed_encoding_t1.setInputMask(_ydl_ffmpeg_qt_time_mask)
        self.timed_encoding_t2.setInputMask(_ydl_ffmpeg_qt_time_mask)
        font = QFont("Courier",8,True)
        fm = QFontMetrics(font)
        self.timed_encoding_t1.setFixedSize(fm.width(_ydl_ffmpeg_qt_width_mask), fm.height())
        self.timed_encoding_t2.setFixedSize(fm.width(_ydl_ffmpeg_qt_width_mask), fm.height())
        self.timed_encoding_t1.setFont(font)
        self.timed_encoding_t2.setFont(font)

        self.timed_encoding_t1.setText(info.t1)
        self.timed_encoding_t2.setText(info.t2)
        
        time_layout.addWidget(QLabel('Start'))
        time_layout.addWidget(self.timed_encoding_t1)
        time_layout.addWidget(QLabel('End'))
        time_layout.addWidget(self.timed_encoding_t2)
        self.time_group.setLayout(time_layout)
        self.time_group.setChecked(self.info.use_time)
        
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("Output File"))
        self.output_file = QLineEdit(info.filename)
        output_layout.addWidget(self.output_file)
        
        user_layout = QHBoxLayout()
        self.accept_btn = QPushButton("Accept")
        self.reject_btn = QPushButton("Reject")
        self.accept_btn.clicked.connect(self.accept)
        self.reject_btn.clicked.connect(self.reject)
        user_layout.addWidget(self.accept_btn)
        user_layout.addWidget(self.reject_btn)
        
        layout.addWidget(self.bypass_mkv_chk)
        layout.addWidget(self.time_group)
        layout.addRow(output_layout)
        layout.addRow(user_layout)
        self.setLayout(layout)
        self.setWindowTitle("FFMpeg Setting")
            
    def timedencoding_state_changed(self):
        if self.time_group.isChecked():
            self.timed_encoding_t1.setEnabled(True)
            self.timed_encoding_t2.setEnabled(True)
            self.info.use_time = True
        else:
            self.timed_encoding_t1.setEnabled(False)
            self.timed_encoding_t2.setEnabled(False)
            self.info.use_time = False
        
    def get_t1(self):
        return self.timed_encoding_t1.text()
        
    def get_t2(self):
        return self.timed_encoding_t2.text()

    def get_filename(self):
        return self.output_file.text()
        
    def get_bypass(self):
        return self.bypass_mkv_chk.isChecked()

#http://stackoverflow.com/questions/9166087/move-row-up-and-down-in-pyqt4
def move_item_down(table):
    rcount = table.rowCount()
    ccount = table.columnCount()
    if rcount <= 0: return
    
    row = table.currentRow()
    column = table.currentColumn();
    if row < rcount-1:
        table.insertRow(row+2)
        for i in range(ccount):
            table.setItem(row+2,i,table.takeItem(row,i))
            table.setCurrentCell(row+2,column)
        table.removeRow(row)        

def move_item_up(table):    
    rcount = table.rowCount()
    ccount = table.columnCount()
    if rcount <= 0: return

    row = table.currentRow()
    column = table.currentColumn();
    if row > 0:
        table.insertRow(row-1)
        for i in range(ccount):
            table.setItem(row-1,i,table.takeItem(row+1,i))
            table.setCurrentCell(row-1,column)
        table.removeRow(row+1)        

def delete_all_item(table, format_cmb=None):
    
    for i in reversed(range(table.rowCount())):
        table.removeRow(i)
    table.setRowCount(0)
    
    if format_cmb != None: 
        format_cmb.clear()
    
def delete_item(table, format_cmb=None):

    row = table.currentRow()
    row_count = table.rowCount()
    
    if row_count == 0: return
    
    if row_count == 1: delete_all_item(table, format_cmb)
    else:
        column = table.currentColumn();
        for i in range(table.columnCount()):
            table.setItem(row,i,table.takeItem(row+1,i))
            table.setCurrentCell(row,column)
        table.removeRow(row+1)
        table.setRowCount(row_count-1)
        
    if format_cmb != None:
        format_cmb.removeItem(row+1)
        
class QProcessProgress(QProcess):
    def __init__(self, key):
        super(QProcessProgress, self).__init__()
        self.key = key
        self.step = 0
        self.file_exist = False
        self.error = False
        self.status = ""
 
#-------------------------------------------------------------------------------
# Reference: 
# https://stackoverflow.com/questions/50930792/pyqt-multiple-qprocess-and-output
#-------------------------------------------------------------------------------
 
class ProcessController(QObject):

    status_changed = pyqtSignal(QObject)

    def __init__(self, job_list, formula = "Proc %d"):
        super(ProcessController, self).__init__()
        self.job_list = job_list
        self.nproc = 0
        self.proc_pool = None
        self.key_formula = formula

    def start(self):
        self.proc_pool = OrderedDict()
        self.nproc = 0
        
        for k, _ in enumerate(self.job_list):
            key = self.key_formula%(k+1)
            proc = QProcessProgress(key)
            proc.setReadChannel(QProcess.StandardOutput)
            proc.setProcessChannelMode(QProcess.MergedChannels)
            proc.finished.connect(partial(self.check_finshed,key))
            proc.readyRead.connect(partial(self.read_data,key))
            self.proc_pool[key] = proc
            self.nproc += 1

        for j, p in zip(self.job_list, self.proc_pool.values()):
            p.start(j[0], j[1])
            
    def check_finshed(self, key):
        if not self.proc_pool: 
            return
        
        self.nproc -= 1
        if not self.proc_pool[key].file_exist:
            self.proc_pool[key].status = "finished"
            self.proc_pool[key].step = 100
            self.status_changed.emit(self.proc_pool[key])
        
    def kill(self):
        if self.proc_pool:
            for p in self.proc_pool.values():
                p.kill()
                
    def delete_process(self):
        self.proc_pool = None
        self.nproc = 0
        
    def read_data(self, key):
        try:
            data = str(self.proc_pool[key].readLine(), 'cp949') # For Windows
        except Exception as e:
            proc.error = True
            proc.status = "=> [%s] : %s\n%s"%(key, _exception_msg(e), data)
            proc.step = 100
            self.status_changed.emit(proc)
            return
            
        proc = self.proc_pool[key]
        if _find_ydl_error(data):
            proc.error = True
            proc.status = data
            proc.step = 100
            self.status_changed.emit(proc)
            return
            
        if _file_exist(data):
            proc.file_exist = True
            proc.status = "already exist"
            proc.step = 100
            self.status_changed.emit(proc)
            return
                       
        match = _find_percent.search(data)
        if match:
            self.proc_pool[key].step = int(float(match.group(0)[:-1]))

# ---------------------------------------------------------------------
# Non-modal dialogue            
# https://stackoverflow.com/questions/38309803/pyqt-non-modal-dialog-always-modal
# ---------------------------------------------------------------------

class ProcessTracker(QDialog):

    status_changed = pyqtSignal(int)
    
    #def __init__(self, proc_ctrl, msg):  # modal
    def __init__(self, parent, proc_ctrl, msg): # modaless/non-modal
        #super(ProcessTracker, self).__init__() # modal
        QDialog.__init__(self, parent) # non-modal
        self.setModal(0) # non-modal
        
        self.proc_ctrl = proc_ctrl
        self.msg = msg
        self.initUI()
        
    def initUI(self):
        import icon_exit
        import icon_download
        import icon_cancel
        layout = QFormLayout()
        
        self.widget = QWidget()
        
        grid = QGridLayout()
        self.progress_bars = OrderedDict()
        
        for k, _ in enumerate(self.proc_ctrl.job_list):
            # You need to change ProcessController.start also as follows:
            #  k --> (k+1)
            key = self.proc_ctrl.key_formula%(k+1)
            grid.addWidget(QLabel(key), k, 0)
            p_bar = QProgressBar()
            self.progress_bars[key] = p_bar
            grid.addWidget(p_bar, k, 1)
        
        self.widget.setLayout(grid)
        self.scroll = QScrollArea()
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll.setMaximumHeight(200)
        self.scroll.setWidget(self.widget)
        self.scroll.setWidgetResizable(True)
        
        self.start_btn = QPushButton()
        self.start_btn.setIcon(QIcon(QPixmap(icon_download.table)))
        self.start_btn.setIconSize(QSize(32,32))
        self.start_btn.clicked.connect(self.start_download)
        
        self.cancel_btn = QPushButton()
        self.cancel_btn.setIcon(QIcon(QPixmap(icon_cancel.table)))
        self.cancel_btn.setIconSize(QSize(32,32))
        self.cancel_btn.clicked.connect(self.cancel_download)

        self.exit_btn = QPushButton()
        self.exit_btn.setIcon(QIcon(QPixmap(icon_exit.table)))
        self.exit_btn.setIconSize(QSize(32,32))
        self.exit_btn.clicked.connect(self.exit_download)
        
        option = QHBoxLayout()
        option.addWidget(self.start_btn)
        option.addWidget(self.cancel_btn)
        option.addWidget(self.exit_btn)
        
        layout.addWidget(self.scroll)
        layout.addRow(option)
        
        self.proc_ctrl.status_changed.connect(self.set_download_status)
        self.setWindowTitle("Concurrent Download")
        self.timer = QBasicTimer()
        self.setLayout(layout)

    def keyPressEvent(self, event):
        pass
    
    def timerEvent(self, e):
        if self.proc_ctrl.nproc <= 0:
            self.timer.stop()
            end_time = time.time()
            elasped_time = hms_string(end_time-self.start_time)
            self.msg.appendPlainText("=> Elasped time: {}\n=> Concurrent download Done!\n".format(elasped_time))
            self.enable_download_buttons()
            return
            
        for p in self.proc_ctrl.proc_pool.values():
            self.progress_bars[p.key].setValue(p.step)
            
    def set_download_status(self, proc):
        self.progress_bars[proc.key].setValue(proc.step)
        
    def start_download(self):
        self.status_changed.emit(_ydl_download_start)
        
        for p_bar in self.progress_bars.values():
            p_bar.setValue(0)
            p_bar.setTextVisible(True)
            p_bar.setFormat("Download: %p%")
        self.disable_download_buttons()
        self.start_time = time.time()
        
        if self.timer.isActive():
            self.timer.stop()
        else:
            self.timer.start(100, self)
            
        try:
            self.proc_ctrl.start()
        except (IOError, OSError) as err:
            QMessageBox.question(self, 'Error', "%s"%err)
            self.global_message.appendPlainText("=> Error: %s"%err)
            self.enable_single_download_buttons()        
            
    def disable_download_buttons(self):
        self.start_btn.setEnabled(False)

    def enable_download_buttons(self):
        if self.proc_ctrl.nproc <= 0:
            msg.message_box("Concurrent download finished!", msg.message_normal)
        self.start_btn.setEnabled(True)
        
    def cancel_download(self):
        if self.proc_ctrl.nproc > 0:
            ret = msg.message_box("Download NOT finished!\nDo you want to Quit?", msg.message_yesno)
            if ret == QMessageBox.No: 
                return
        self.proc_ctrl.kill()
        self.start_btn.setEnabled(True)
        
    def preprocess_exit(self):
        self.timer.stop()
        self.proc_ctrl.kill()
        self.proc_ctrl.delete_process()
        self.status_changed.emit(_ydl_download_finish)
        
    def exit_download(self):
        if self.proc_ctrl.nproc > 0:
            ret = msg.message_box("Download NOT finished!\nDo you want to Quit?", msg.message_yesno)
            if ret == QMessageBox.No:
                return
        self.preprocess_exit()
        self.accept()
        
    def closeEvent(self, evnt):
        if self.proc_ctrl.nproc > 0:
            ret = msg.message_box("Download NOT finished!\nDo you want to Quit?", msg.message_yesno)
            if ret == QMessageBox.No: 
                evnt.ignore()
                return
        
        self.preprocess_exit()
        super(ProcessTracker, self).closeEvent(evnt)

# ---------------------------------------------------------------------
# This dialogue is called at multiple download
# ---------------------------------------------------------------------
        
class QYoutubeDownloadFormatDlg(QDialog):
    def __init__(self, url_table, msg):
        super(QYoutubeDownloadFormatDlg, self).__init__()
        self.msg = msg
        self.initUI(url_table)
        
    def initUI(self, url_table):
        self.format_unsable = False
        self.url_table = url_table
        layout = QFormLayout()
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("URL #"))
        self.url_cmb = QComboBox()
        self.url_cmb.addItems([str(x+1) for x in range(url_table.rowCount())])
        url_layout.addWidget(self.url_cmb)
        
        self.youtube_format_tbl = QTableWidget()
        self.youtube_format_tbl.verticalHeader().hide()
        self.youtube_format_tbl.setColumnCount(6)
        self.youtube_format_tbl.setHorizontalHeaderItem(0, QTableWidgetItem("Code"))
        self.youtube_format_tbl.setHorizontalHeaderItem(1, QTableWidgetItem("Ext"))
        self.youtube_format_tbl.setHorizontalHeaderItem(2, QTableWidgetItem("Res"))
        self.youtube_format_tbl.setHorizontalHeaderItem(3, QTableWidgetItem("Bit"))
        self.youtube_format_tbl.setHorizontalHeaderItem(4, QTableWidgetItem("Size"))
        self.youtube_format_tbl.setHorizontalHeaderItem(5, QTableWidgetItem("Type"))

        header = self.youtube_format_tbl.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)        
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)        
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)        
        
        ans_layout = QGridLayout()
        self.fetch_youtube_format_btn = QPushButton('Fetch : Format Retrieve')
        self.fetch_youtube_format_btn.clicked.connect(self.fetch_youtube_format)
        self.no_format = QPushButton("Do Not Use Fromat")
        self.no_format.clicked.connect(self.not_use_format)

        self.direct_format_chk = QCheckBox('Format Input', self)
        self.direct_format_chk.stateChanged.connect(self.direct_format_input)
        self.direct_format =  QLineEdit()
        onlyInt = QIntValidator()
        self.direct_format.setValidator(onlyInt)
        self.direct_format.setEnabled(False)
        
        
        self.ok = QPushButton('OK')
        self.cancel = QPushButton('CANCEL')
        self.ok.clicked.connect(self.accept)
        self.cancel.clicked.connect(self.reject)
        
        ans_layout.addWidget(self.fetch_youtube_format_btn, 0, 0, 1, 2)
        ans_layout.addWidget(self.no_format, 1, 0, 1, 2)
        
        ans_layout.addWidget(self.direct_format_chk, 2, 0)
        ans_layout.addWidget(self.direct_format, 2, 1)
        
        ans_layout.addWidget(self.cancel, 3, 0, 1, 2)
        ans_layout.addWidget(self.ok, 4, 0, 1, 2)
        
        ans_layout.setContentsMargins(0,0,0,0)
        ans_layout.setSpacing(5)
        
        layout.addRow(url_layout)
        layout.addWidget(self.youtube_format_tbl)
        layout.addRow(ans_layout)
        self.setLayout(layout)
        self.setWindowTitle("Fetch Format")
        
    def direct_format_input(self):
        if self.direct_format_chk.isChecked():
            self.direct_format.setEnabled(True)
        else:
            self.direct_format.setEnabled(False)
        
    def not_use_format(self):
        self.format_unsable = True
        self.accept()
        
    def fetch_youtube_format(self):
        delete_all_item(self.youtube_format_tbl, None)
        url = self.url_table.item(self.url_cmb.currentIndex(),0).text()
        fetch_youtube_format_from_url(url, self.youtube_format_tbl, self.msg)
        
    def get_format(self):
        fmt = self.direct_format.text()
        row = self.youtube_format_tbl.currentRow()
        return fmt if self.direct_format_chk.isChecked() and  fmt != ""\
                else self.youtube_format_tbl.item(row, 0).text()\
                if row >= 0 else _ydl_format_none
                  
# ---------------------------------------------------------------------
#                  YOUTUBE DOWNLOADER
# ---------------------------------------------------------------------

#https://arcpy.wordpress.com/2012/04/20/146/    
def hms_string(sec_elapsed):
    h = int(sec_elapsed / (60 * 60))
    m = int((sec_elapsed % (60 * 60)) / 60)
    s = sec_elapsed % 60.
    return "{}:{:>02}:{:>05.2f}".format(h, m, s)

class QYoutubeDownloader(QWidget):
    def __init__(self):
        super(QYoutubeDownloader, self).__init__()
        self.single_download_ffmpeg_config = PostprocessSingleDownload()
        self.initUI()

    def initUI(self):
        self.form_layout  = QFormLayout()
        tab_layout = QVBoxLayout()
        self.tabs = QTabWidget()
        policy = self.tabs.sizePolicy()
        policy.setVerticalStretch(1)
        self.tabs.setSizePolicy(policy)
        self.tabs.setEnabled(True)
        self.tabs.setTabPosition(QTabWidget.West)
        self.tabs.setObjectName('Media List')
        
        self.youtube_tab    = QWidget()
        self.message_tab    = QWidget()
        
        self.tabs.addTab(self.youtube_tab, get_youtubetab_text())
        self.tabs.addTab(self.message_tab, get_messagetab_text())
        
        self.youtube_download_tab_UI()
        self.message_tab_UI()
        
        tab_layout.addWidget(self.tabs)
        self.form_layout.addRow(tab_layout)
        self.setLayout(self.form_layout)
        self.setWindowTitle("YDL")
        self.setWindowIcon(QIcon(QPixmap(icon_youtube.table)))
        self.show()
    
    def timerEvent(self, e):
    
        if self.process_single:
            self.single_download_progress.setValue(self.single_download_step)
            
        if self.process_multiple:
            self.multiple_download_progress.setValue(self.multiple_download_step)
    
    def clear_global_message(self):
        self.global_message.clear()
        
    def message_tab_UI(self):
        layout = QVBoxLayout()
        
        clear = QPushButton('Clear', self)
        clear.clicked.connect(self.clear_global_message)
        
        self.global_message = QPlainTextEdit()
        layout.addWidget(clear)
        layout.addWidget(self.global_message)
        self.message_tab.setLayout(layout)

    def youtube_download_tab_UI(self):
        layout = QFormLayout()
        
        grid = QGridLayout()
        grid.addWidget(QLabel("Folder"), 0,0)
        self.youtube_save_path = QLineEdit()
        self.youtube_save_path.setText(os.getcwd())  
        
        self.youtube_save_path_btn = QPushButton()
        self.youtube_save_path_btn.setIcon(QIcon(QPixmap(icon_folder_open.table)))
        self.youtube_save_path_btn.setIconSize(QSize(16,16))
        self.youtube_save_path_btn.clicked.connect(self.get_new_youtube_download_path)
        
        grid.addWidget(self.youtube_save_path, 0, 1)
        grid.addWidget(self.youtube_save_path_btn, 0, 2)

        self.youtube_tabs = QTabWidget()
        policy = self.youtube_tabs.sizePolicy()
        self.youtube_tabs.setSizePolicy(policy)
        self.youtube_tabs.setEnabled(True)
        self.youtube_tabs.setTabPosition(QTabWidget.North)
        self.youtube_tabs.setObjectName('Youtube List')
    
        self.single_video_tab   = QWidget()
        self.multiple_video_tab = QWidget()
        self.youtubedl_setting_tab = QWidget()
        
        self.youtube_tabs.addTab(self.single_video_tab, get_single_tab_text())
        self.youtube_tabs.addTab(self.multiple_video_tab, get_multiple_tab_text())
        self.youtube_tabs.addTab(self.youtubedl_setting_tab, get_youtubedl_setting_tab_text())
        self.youtube_tabs.currentChanged.connect(self.youtube_video_tab_changed)
        self.single_video_tab_UI()
        self.multiple_video_tab_UI()
        
        self.time_font = QFont("Courier",11,True)
        self.single_download_timer = QBasicTimer()
        self.multiple_download_timer = QBasicTimer()
        
        self.process_single = None
        self.process_multiple = None

        layout.addRow(grid)
        layout.addRow(self.youtube_tabs)
        self.youtube_tab.setLayout(layout)
        
    def get_new_youtube_download_path(self):
        startingDir = os.getcwd() 
        path = QFileDialog.getExistingDirectory(None, 'Save folder', startingDir, 
        QFileDialog.ShowDirsOnly)
        if not path: return
        self.youtube_save_path.setText(path)
        #os.chdir(path)    
        
    def youtube_video_tab_changed(self):
        pass
        
    def single_video_tab_UI(self):
        import icon_media_edit
        
        # single video download
        layout = QFormLayout()
        grid = QGridLayout()
        grid.addWidget(QLabel("URL"), 1,0)
        self.youtube_url = QLineEdit()
        grid.addWidget(self.youtube_url, 1, 1)
        
        self.youtube_format_tbl = QTableWidget()
        self.youtube_format_tbl.verticalHeader().hide()
        self.youtube_format_tbl.setColumnCount(6)
        self.youtube_format_tbl.setHorizontalHeaderItem(0, QTableWidgetItem("Code"))
        self.youtube_format_tbl.setHorizontalHeaderItem(1, QTableWidgetItem("Ext"))
        self.youtube_format_tbl.setHorizontalHeaderItem(2, QTableWidgetItem("Res"))
        self.youtube_format_tbl.setHorizontalHeaderItem(3, QTableWidgetItem("Bit"))
        self.youtube_format_tbl.setHorizontalHeaderItem(4, QTableWidgetItem("Size"))
        self.youtube_format_tbl.setHorizontalHeaderItem(5, QTableWidgetItem("Type"))

        header = self.youtube_format_tbl.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)        
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        
        grid_btn = QGridLayout()
        self.fetch_youtube_format_btn = QPushButton('', self)
        self.fetch_youtube_format_btn.setIcon(QIcon(QPixmap(icon_request_format.table)))
        self.fetch_youtube_format_btn.setIconSize(QSize(24,24))
        self.fetch_youtube_format_btn.setToolTip("Fetch fromats from the URL")
        self.fetch_youtube_format_btn.clicked.connect(self.fetch_youtube_format)
  
        self.delete_btn = QPushButton('', self)
        self.delete_btn.setIcon(QIcon(QPixmap(icon_delete_url.table)))
        self.delete_btn.setIconSize(QSize(24,24))
        self.delete_btn.setToolTip("Delete a format")
        # for connection see the definition of self.choose_format_cmb after group bottons
        
        self.delete_all_btn = QPushButton('', self)
        self.delete_all_btn.setIcon(QIcon(QPixmap(icon_trash_url.table)))
        self.delete_all_btn.setIconSize(QSize(24,24))
        self.delete_all_btn.setToolTip("Delete all formats")
        # for connection see the definition of self.choose_format_cmb after group bottons
        
        self.set_single_download_ffmpeg_config_btn = QPushButton()
        self.set_single_download_ffmpeg_config_btn.setIcon(QIcon(QPixmap(icon_media_edit.table)))
        self.set_single_download_ffmpeg_config_btn.setIconSize(QSize(24,24))
        self.set_single_download_ffmpeg_config_btn.setToolTip("Single download setting")
        self.set_single_download_ffmpeg_config_btn.clicked.connect(self.set_single_download_ffmpeg_config)

        grid_btn.addWidget(self.fetch_youtube_format_btn, 0, 0)
        grid_btn.addWidget(self.delete_btn, 0, 1)
        grid_btn.addWidget(self.delete_all_btn, 0, 2)
        grid_btn.addWidget(self.set_single_download_ffmpeg_config_btn, 0,3)

        self.single_download_audio_codec_cmb = QComboBox()
        self.single_download_audio_codec_cmb.addItems(_ydl_audio_codec)
        
        self.single_download_audio_quality_cmb = QComboBox()
        self.single_download_audio_quality_cmb.addItems(_ydl_audio_quality)
        
        self.single_download_video_codec_cmb = QComboBox()
        self.single_download_video_codec_cmb.addItems(_ydl_video_codec)
        
        grid_option_btn = QGridLayout()
        grid_option_btn.addWidget(self.single_download_audio_codec_cmb, 2,0)
        grid_option_btn.addWidget(self.single_download_audio_quality_cmb, 2,1)
        grid_option_btn.addWidget(self.single_download_video_codec_cmb, 2,2)
        
        # default audio quality for ffmpeg is 5
        self.single_download_audio_quality_cmb.setCurrentIndex(5)
        
        self.single_download_progress = QProgressBar(self)
        grid_option_btn.addWidget(self.single_download_progress, 4,0, 1, 3)
        
        #av_group = QGroupBox()
        moods = [QRadioButton("Audio"), QRadioButton("Video")]
        # Set a radio button to be checked by default
        moods[1].setChecked(True)   

        button_layout = QHBoxLayout()
        # Create a button group for radio buttons: Audio / video
        self.mood_av_button_group = QButtonGroup()
        
        for i in range(len(moods)):
            # Add each radio button to the button layout
            button_layout.addWidget(moods[i])
            # Add each radio button to the button group & give it an ID of i
            self.mood_av_button_group.addButton(moods[i], i)
            # Connect each radio button to a method to run when it's clicked
            #self.connect(moods[i], SIGNAL("clicked()"), self.single_download_AV_codec_clicked)
            moods[i].clicked.connect(self.single_download_AV_codec_clicked)

        self.single_download_AV_codec_clicked()
        grid_option_btn.addLayout(button_layout, 1, 0, 1, 2)
        
        self.choose_format_cmb = QComboBox()
        grid_option_btn.addWidget(self.choose_format_cmb, 3,2)
        
        self.delete_btn.clicked.connect(partial(delete_item, self.youtube_format_tbl, self.choose_format_cmb))
        self.delete_all_btn.clicked.connect(partial(delete_all_item, self.youtube_format_tbl, self.choose_format_cmb))

        self.direct_format_chk = QCheckBox("User Format")
        self.direct_format_chk.stateChanged.connect(self.direct_format_input)
        
        self.direct_format = QLineEdit()
        self.direct_format.setMaximumWidth(90)
        onlyInt = QIntValidator()
        self.direct_format.setValidator(onlyInt)
        self.direct_format.setEnabled(False)
        
        grid_option_btn.addWidget(self.direct_format_chk, 3, 0)
        grid_option_btn.addWidget(self.direct_format, 3, 1)
        grid_option_btn.setContentsMargins(0,0,0,0)
        grid_option_btn.setSpacing(5)
        
        run_option = QHBoxLayout()
        self.start_single_download_btn = QPushButton()
        self.start_single_download_btn.setIcon(QIcon(QPixmap(icon_download.table)))
        self.start_single_download_btn.setIconSize(QSize(32,32))
        self.start_single_download_btn.clicked.connect(self.start_single_download)
        
        self.cancel_single_download_btn = QPushButton()
        self.cancel_single_download_btn.setIcon(QIcon(QPixmap(icon_cancel.table)))
        self.cancel_single_download_btn.setIconSize(QSize(32,32))
        self.cancel_single_download_btn.clicked.connect(self.cancel_single_download)
        
        run_option.addWidget(self.start_single_download_btn)
        run_option.addWidget(self.cancel_single_download_btn)
        
        layout.addRow(grid)
        layout.addRow(self.youtube_format_tbl)
        layout.addRow(grid_btn)
        layout.addRow(grid_option_btn)
        layout.addRow(run_option)
        
        self.single_video_tab.setLayout(layout)
        
    def set_single_download_ffmpeg_config(self):
        dlg = PostprocessSingleDownloadDlg(self.single_download_ffmpeg_config)
        res = dlg.exec_()

        if res == QDialog.Accepted:
            self.single_download_ffmpeg_config.use_ffmpeg = True
            self.single_download_ffmpeg_config.bypass_mkv = dlg.get_bypass()
            
            if self.single_download_ffmpeg_config.use_time:
                t1 = dlg.get_t1()
                t2 = dlg.get_t2()
                
                match1 = _check_time.search(t1)
                match2 = _check_time.search(t2)
        
                if not match1 or not match2:
                    msg.message_box("Invalid time format(start or end)!", msg.message_warning)
                    self.global_message.appendPlainText("=> Error\nT1 : %s\nT2 : %s\n"%(t1,t2))
                    return

                self.single_download_ffmpeg_config.t1 = t1
                self.single_download_ffmpeg_config.t2 = t2
            self.single_download_ffmpeg_config.filename = dlg.get_filename()
        else:
            self.single_download_ffmpeg_config.use_ffmpeg = False
            
    def direct_format_input(self):
        if self.direct_format_chk.isChecked():
            self.direct_format.setEnabled(True)
        else:
            self.direct_format.setEnabled(False)
    
    def single_download_AV_codec_clicked(self):
        id = self.mood_av_button_group.checkedId()
        if id == 0:
            self.single_download_audio_codec_cmb.setEnabled(True)
            self.single_download_audio_quality_cmb.setEnabled(True)
            self.single_download_video_codec_cmb.setEnabled(False)
        elif id == 1:
            self.single_download_audio_codec_cmb.setEnabled(False) 
            self.single_download_audio_quality_cmb.setEnabled(False)            
            self.single_download_video_codec_cmb.setEnabled(True)

    def single_video_checked(self):
        if self.single_video_chk.isChecked():
            self.single_audio_only_chk.setEnabled(False)
            self.single_download_audio_codec_cmb.setEnabled(False)
        else:
            self.single_audio_only_chk.setEnabled(True)
            self.single_download_audio_codec_cmb.setEnabled(True)
    
    def single_audio_only_checked(self):
        if self.single_audio_only_chk.isChecked():
            self.single_video_chk.setEnabled(False)
            self.single_download_video_codec_cmb.setEnabled(False)
        else:
            self.single_download_video_codec_cmb.setEnabled(True)
            self.single_video_chk.setEnabled(True)
        
    def get_current_youtube_table(self):
        return  self.youtube_format_tbl\
                if self.youtube_tabs.tabText(self.youtube_tabs.currentIndex()) ==\
                get_single_tab_text() else self.youtube_path_tbl
        

    def multiple_video_tab_UI(self):
        import icon_arrow_down
        import icon_arrow_up
        
        layout = QFormLayout()
        
        self.youtube_path_tbl = QTableWidget()
        self.youtube_path_tbl.setColumnCount(3)
        self.youtube_path_tbl.setHorizontalHeaderItem(0, QTableWidgetItem("URL"))
        self.youtube_path_tbl.setHorizontalHeaderItem(1, QTableWidgetItem("Description"))
        self.youtube_path_tbl.setHorizontalHeaderItem(2, QTableWidgetItem("Status"))

        grid_table_btn = QGridLayout()
        self.add_url_btn = QPushButton('', self)
        self.add_url_btn.setIcon(QIcon(QPixmap(icon_add_row.table)))
        self.add_url_btn.setIconSize(QSize(24,24))
        self.add_url_btn.setToolTip("Add URL")
        self.add_url_btn.clicked.connect(self.add_url)

        self.move_url_up_btn = QPushButton('', self)
        self.move_url_up_btn.setIcon(QIcon(QPixmap(icon_arrow_up.table)))
        self.move_url_up_btn.setIconSize(QSize(24,24))
        self.move_url_up_btn.setToolTip("Move a URL up")
        self.move_url_up_btn.clicked.connect(partial(move_item_up, self.youtube_path_tbl))

        self.move_url_down_btn = QPushButton('', self)
        self.move_url_down_btn.setIcon(QIcon(QPixmap(icon_arrow_down.table)))
        self.move_url_down_btn.setIconSize(QSize(24,24))
        self.move_url_down_btn.setToolTip("Move a URL down")
        self.move_url_down_btn.clicked.connect(partial(move_item_down, self.youtube_path_tbl))
        
        self.delete_btn = QPushButton('', self)
        self.delete_btn.setIcon(QIcon(QPixmap(icon_delete_url.table)))
        self.delete_btn.setIconSize(QSize(24,24))
        self.delete_btn.setToolTip("Delete a URL")
        self.delete_btn.clicked.connect(partial(delete_item, self.youtube_path_tbl, None))
        
        self.delete_all_btn = QPushButton('', self)
        self.delete_all_btn.setIcon(QIcon(QPixmap(icon_trash_url.table)))
        self.delete_all_btn.setIconSize(QSize(24,24))
        self.delete_all_btn.setToolTip("Delete All URLs")
        self.delete_all_btn.clicked.connect(partial(delete_all_item, self.youtube_path_tbl, None))

        grid_table_btn.addWidget(self.add_url_btn, 0, 0)
        grid_table_btn.addWidget(self.move_url_up_btn, 0, 1)
        grid_table_btn.addWidget(self.move_url_down_btn, 0, 2)
        grid_table_btn.addWidget(self.delete_btn, 0, 3)

        self.load_json_btn = QPushButton('', self)
        self.load_json_btn.setIcon(QIcon(QPixmap(icon_json.table)))
        self.load_json_btn.setIconSize(QSize(24,24))
        self.load_json_btn.setToolTip("Load a list of URLs with JSON format")
        self.load_json_btn.clicked.connect(self.load_json)
        
        self.save_json_btn = QPushButton('', self)
        self.save_json_btn.setIcon(QIcon(QPixmap(icon_save.table)))
        self.save_json_btn.setIconSize(QSize(24,24))
        self.save_json_btn.setToolTip("Save the list of URLs as JSON format")
        self.save_json_btn.clicked.connect(self.save_json)

        self.global_download_format_btn = QPushButton('Fmt: {}'.format(_ydl_format_none), self)
        self.global_download_format_btn.clicked.connect(self.choose_global_download_format)

        grid_table_btn.addWidget(self.load_json_btn, 1, 0)
        grid_table_btn.addWidget(self.save_json_btn, 1, 1)
        grid_table_btn.addWidget(self.delete_all_btn, 1, 2)
        
        grid_option_btn = QGridLayout()
        
        self.multiple_download_audio_codec_cmb = QComboBox()
        self.multiple_download_audio_codec_cmb.addItems(_ydl_audio_codec)
        
        self.multiple_download_audio_quality_cmb = QComboBox()
        self.multiple_download_audio_quality_cmb.addItems(_ydl_audio_quality)
        
        self.multiple_download_video_codec_cmb = QComboBox()
        self.multiple_download_video_codec_cmb.addItems(_ydl_video_codec)
        
        grid_option_btn.addWidget(self.multiple_download_audio_codec_cmb, 1,0)
        grid_option_btn.addWidget(self.multiple_download_audio_quality_cmb, 1,1)
        grid_option_btn.addWidget(self.multiple_download_video_codec_cmb, 1,2)

        # default audio quality for ffmpeg is 5
        self.multiple_download_audio_quality_cmb.setCurrentIndex(5)
        
        #av_group = QGroupBox()
        moods = [QRadioButton("Audio"), QRadioButton("Video")]
        # Set a radio button to be checked by default
        moods[1].setChecked(True)   

        button_layout = QHBoxLayout()
        # Create a button group for radio buttons: Audio / video
        self.multiple_mood_AV_button_group = QButtonGroup()
        
        for i in range(len(moods)):
            # Add each radio button to the button layout
            button_layout.addWidget(moods[i])
            # Add each radio button to the button group & give it an ID of i
            self.multiple_mood_AV_button_group.addButton(moods[i], i)
            # Connect each radio button to a method to run when it's clicked
            #self.connect(moods[i], SIGNAL("clicked()"), self.multiple_download_AV_codec_clicked)
            moods[i].clicked.connect(self.multiple_download_AV_codec_clicked)

        self.multiple_download_AV_codec_clicked()
        grid_option_btn.addLayout(button_layout, 0, 0, 1, 2)
        grid_option_btn.addWidget(self.global_download_format_btn, 0, 3)

        self.multiple_download_method = QComboBox()
        self.multiple_download_method.addItems(_ydl_multiple_download_method)
        grid_option_btn.addWidget(self.multiple_download_method, 1, 3)
        
        self.multiple_download_progress = QProgressBar(self)
        grid_option_btn.addWidget(self.multiple_download_progress, 2, 0, 1, 4)

        grid_option_btn.setContentsMargins(0,0,0,0)
        grid_option_btn.setSpacing(5)
        
        run_option = QHBoxLayout()
        self.start_multiple_download_btn = QPushButton()
        self.start_multiple_download_btn.setIcon(QIcon(QPixmap(icon_download.table)))
        self.start_multiple_download_btn.setIconSize(QSize(32,32))
        self.start_multiple_download_btn.clicked.connect(self.start_multiple_download)
        
        self.cancel_multiple_download_btn = QPushButton()
        self.cancel_multiple_download_btn.setIcon(QIcon(QPixmap(icon_cancel.table)))
        self.cancel_multiple_download_btn.setIconSize(QSize(32,32))
        self.cancel_multiple_download_btn.clicked.connect(self.cancel_multiple_download)
        
        run_option.addWidget(self.start_multiple_download_btn)
        run_option.addWidget(self.cancel_multiple_download_btn)
        
        layout.addRow(self.youtube_path_tbl)
        layout.addRow(grid_table_btn)
        layout.addRow(grid_option_btn)
        layout.addRow(run_option)
        
        self.multiple_video_tab.setLayout(layout)
        
    def save_json(self):
        count = self.youtube_path_tbl.rowCount()
        if count == 0: return

        json_export_file = 'ydl_url_list.json'
        json_save_path = os.path.join(self.youtube_save_path.text(), json_export_file)
        json_save_file = QFileDialog.getSaveFileName(None, 'Save File', json_save_path, 
                         'JSON files (*.json);;All files (*)')
        
        data = OrderedDict()
        v_list = list()
        
        for k in range(count):
            url = self.youtube_path_tbl.item(k,0).text()
            desc = self.youtube_path_tbl.item(k,1).text()
            v_list.append({"desc": desc, "url": url})
        data["videos"] = v_list
            
        try:
            with open(json_save_file, 'w') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            self.global_message.appendPlainText("=> Error(save_json) : %s"%str(e))
            msg.message_box(str(e), msg.message_error)
        self.global_message.appendPlainText("URL saved at %s"%json_save_file)
        msg.message_box("URL saved at %s"%json_save_file, msg.message_normal)
            
    def load_json(self):
        file = QFileDialog.getOpenFileName(self, "Load JSON", 
                directory=self.youtube_save_path.text(), 
                filter="Json (*.json );;All files (*.*)")

        file = file[0] # uncomment this line for PyQt5
        
        if file: 
            path, fname = os.path.split(file)
            
            try:
                with open(file) as f:
                    videos = json.load(f)["videos"]
                    cur_row = self.youtube_path_tbl.rowCount()
                    for k, v in enumerate(videos):
                        self.youtube_path_tbl.insertRow(cur_row+k)
                        self.youtube_path_tbl.setItem(cur_row+k, 0, 
                            QTableWidgetItem(v["url"]))
                        self.youtube_path_tbl.setItem(cur_row+k, 1, 
                            QTableWidgetItem(v["desc"]))
                        self.youtube_path_tbl.setItem(cur_row+k, 2, 
                            QTableWidgetItem(""))                            
                    self.global_message.appendPlainText("=> Load Json: total vidoe(%d)"%(k+1))
            except Exception as e:
                msg.message_box(str(e), msg.message_error)
                return
        
    def choose_global_download_format(self):
        nurl = self.youtube_path_tbl.rowCount()
        if nurl == 0: return
        format_dlg = QYoutubeDownloadFormatDlg(self.youtube_path_tbl, self.global_message)
        ret = format_dlg.exec_()
        if ret == 1:
            fmt = format_dlg.get_format()
            self.global_download_format_btn.setText("Fmt: {}".format(fmt))
        
    def multiple_download_AV_codec_clicked(self):
        id = self.multiple_mood_AV_button_group.checkedId()
        if id == 0:
            self.multiple_download_audio_codec_cmb.setEnabled(True)
            self.multiple_download_audio_quality_cmb.setEnabled(True)
            self.multiple_download_video_codec_cmb.setEnabled(False)
        elif id == 1:
            self.multiple_download_audio_codec_cmb.setEnabled(False) 
            self.multiple_download_audio_quality_cmb.setEnabled(False)            
            self.multiple_download_video_codec_cmb.setEnabled(True)    
            
    def add_url(self):
        cur_row = self.youtube_path_tbl.rowCount()
        self.youtube_path_tbl.insertRow(cur_row)
        self.youtube_path_tbl.setItem(cur_row, 0, QTableWidgetItem(""))
        self.youtube_path_tbl.setItem(cur_row, 1, QTableWidgetItem(""))
        self.youtube_path_tbl.setItem(cur_row, 2, QTableWidgetItem(""))
        
    def fetch_youtube_format(self):
                
        self.global_message.appendPlainText("=> Fetch video formats")
        delete_all_item(self.youtube_format_tbl, self.choose_format_cmb)
        
        frm = fetch_youtube_format_from_url(
            self.youtube_url.text(),
            self.youtube_format_tbl,
            self.global_message)
        if frm:
            self.choose_format_cmb.addItems(frm)
    
    def single_download_data_read(self):
        try:
            #data = str(self.process_single.readAll(), 'utf-8')
            data = str(self.process_single.readLine(), 'cp949') # Windows 
        except Exception as e:
            self.global_message.appendPlainText(_exception_msg(e))
            return

        if _find_ydl_warning(data):
            self.global_message.appendPlainText("=> %s\n"%data)
            
        if _find_ydl_error(data):
            self.process_single_error = True
            msg.message_box(data, msg.message_error)
            return
            
        if _file_exist(data):
            self.single_file_already_exist = True
            msg.message_box(_ydl_const_exist_text, msg.message_normal)
            return

        fn = _find_filename(data)
        if fn:
            fpath, fname = os.path.split(fn.strip())
            self.global_message.appendPlainText("=> Path: %s\n=> Name: %s\n"%(fpath, fname))
            return
                        
        match = _find_percent.search(data)
        if match:
            self.single_download_step = int(float(match.group(0)[:-1]))

    def single_download_finished(self):
        self.enable_single_download_buttons()
        self.single_download_progress.setValue(100)
        self.single_download_timer.stop()
         
        if not self.process_single_error and\
           not self.single_file_already_exist:
            self.print_download_elasped()
        self.process_single = None
         
    def multiple_download_data_read(self):
        try:
            #data = str(self.process_multiple.readAll(), 'utf-8')
            data = str(self.process_multiple.readLine(), 'cp949') # for Windows
        except Exception as e:
            self.global_message.appendPlainText(_exception_msg(e))
            return
        
        if _find_ydl_error(data):
            self.process_multiple_error = True
            self.youtube_path_tbl.item(self.download_count, 0).setBackground(_ydl_color_error)
            self.youtube_path_tbl.item(self.download_count, 2).setText("Error")
            self.global_message.appendPlainText("=> %s\n"%data)
            #msg.message_box("URL: #%d\n%s"%(self.download_count,data), msg.message_error)
            return

        if _file_exist(data):
            self.process_multiple_file_exist = True
            self.youtube_path_tbl.item(self.download_count, 0).setBackground(_ydl_color_file_exist)
            self.youtube_path_tbl.item(self.download_count, 2).setText(_ydl_const_exist_text)
            return

        fn = _find_filename(data)
        if fn:
            fpath, fname = os.path.split(fn.strip())
            self.global_message.appendPlainText("=> Path: %s\n=> Name: %s"%(fpath, fname))
            return

        match = _find_percent.search(data)

        if match:
            self.multiple_download_step = int(float(match.group(0)[:-1]))
            
    def multiple_download_finished(self):
        if len(self.multiple_download_job_list) == 0:
            self.enable_multiple_download_buttons()
            self.multiple_download_progress.setValue(100)
            self.multiple_download_timer.stop()
            self.process_multiple = None

            # check if the last download process has an error
            if self.process_multiple_error is True:
                self.youtube_path_tbl.item(self.download_count, 0).setBackground(_ydl_color_error)
                self.youtube_path_tbl.item(self.download_count, 2).setText("Error")
            elif self.process_multiple_file_exist is False:
                self.youtube_path_tbl.item(self.download_count, 0).setBackground(_ydl_color_finished)
                self.youtube_path_tbl.item(self.download_count, 2).setText("Finished")
            
            self.global_message.appendPlainText("=> Miltiple Download Done")
            self.print_download_elasped()
            return
            
        if self.process_multiple_error is False and self.process_multiple_file_exist is False:
            self.youtube_path_tbl.item(self.download_count, 0).setBackground(_ydl_color_finished)
            self.youtube_path_tbl.item(self.download_count, 2).setText("Finished")
            self.global_message.appendPlainText("=> %d-th download finished\n"%self.download_count)
                
        self.download_count += 1
        
        sublist = self.multiple_download_job_list[0]
        del self.multiple_download_job_list[0]
        
        try:
            self.process_multiple_error = False
            self.process_multiple_file_exis = False
            self.global_message.appendPlainText(self.cmd_to_msg(sublist[0], sublist[1]))
            self.process_multiple.start(sublist[0], sublist[1])
        except (IOError, OSError) as err:
            QMessageBox.question(self, 'Error', "%s"%err)
            self.delete_job_list()
            self.enable_multiple_download_buttons()
                        
    def enable_multiple_download_buttons(self):
        self.start_multiple_download_btn.setEnabled(True)
        
    def disable_multiple_download_buttons(self):
        self.start_multiple_download_btn.setEnabled(False)

    def disable_multiple_parent_buttons(self):
        self.start_multiple_download_btn.setEnabled(False)
        self.cancel_multiple_download_btn.setEnabled(False)
    def enable_multiple_parent_buttons(self):
        self.start_multiple_download_btn.setEnabled(True)
        self.cancel_multiple_download_btn.setEnabled(True)
        
    def print_download_elasped(self):
        download_t2 = time.time()
        elasped_time = hms_string(download_t2-self.download_t1)
        self.global_message.appendPlainText("=> Download Time: {}\n".format(elasped_time))
        msg.message_box("Download Time: {}".format(elasped_time), msg.message_normal)
        
    def delete_job_list(self):
        self.single_download_job_list = []
        self.single_download_timer.stop()

    def enable_single_download_buttons(self):
        self.start_single_download_btn.setEnabled(True)
        
    def disable_single_download_buttons(self):
        self.start_single_download_btn.setEnabled(False)
        
    def cancel_multiple_download(self):
        if not self.process_multiple: return
        if self.multiple_download_method.currentText() == get_sequential_download_text():
            self.global_message.appendPlainText("=> Cancel Multiple Download")
            self.single_download_timer.stop()
            self.multiple_download_job_list.clear()
            self.process_multiple.kill()
        
    def start_multiple_download(self):
        number_of_url = self.youtube_path_tbl.rowCount()
        if number_of_url == 0: 
            msg.message_box("No URL exist!!", msg.message_normal)
            return
            
        tab_text = self.youtube_tabs.tabText(self.youtube_tabs.currentIndex())
        
        arg_list = ['youtube-dl']
        self.multiple_download_step = 0
            
        if tab_text == get_multiple_tab_text():    
            id = self.multiple_mood_AV_button_group.checkedId()
            fmt = self.global_download_format_btn.text()

            if fmt.find(_ydl_format_none) < 0:
                arg_list.extend(["-f", re.search("\d+", fmt).group(0)])
            else:
                if id == 0: # audio only
                    audio_codec = self.multiple_download_audio_codec_cmb.currentText()
                    arg_list.extend([ _ydl_option_extract_audio,
                                      _ydl_option_audio_format,
                                      audio_codec])
                                    
                    if audio_codec != _ydl_best_audio_codec:
                        arg_list.extend([_ydl_option_audio_quality, 
                                        self.multiple_download_audio_quality_cmb.currentText().split(' ')[0]])
                
                elif id == 1: # video
                    if self.multiple_download_video_codec_cmb.currentIndex() > 0:
                        arg_list.extend([_ydl_option_encode_video,
                                        self.multiple_download_video_codec_cmb.currentText()])
                                     
            save_folder = os.path.join(self.youtube_save_path.text(), _ydl_option_output_filename)
            arg_list.extend([_ydl_option_output, save_folder])

            self.multiple_download_job_list = []
            arg_list.append(' ')
            
            for k in range(number_of_url):
                self.youtube_path_tbl.item(k,0).setBackground(QColor(255,255,255))
                self.youtube_path_tbl.item(k,2).setText("")
                arg_list[-1] = self.youtube_path_tbl.item(k,0).text().strip()
                job = [arg_list[0], arg_list[1:]]
                self.multiple_download_job_list.append(job)

            dm = self.multiple_download_method.currentText()
            
            if dm == get_sequential_download_text():
                self.process_multiple = QProcess(self)
                self.process_multiple.setReadChannel(QProcess.StandardOutput)
                self.process_multiple.setProcessChannelMode(QProcess.MergedChannels)
                self.process_multiple.finished.connect(self.multiple_download_finished)
                self.process_multiple.readyRead.connect(self.multiple_download_data_read)
            
                sublist = self.multiple_download_job_list[0]
                del self.multiple_download_job_list[0]
                
                if self.single_download_timer.isActive():
                    self.multiple_download_timer.stop()
                else:
                    self.multiple_download_timer.start(100, self)
                
                self.multiple_download_progress.setTextVisible(True)
                self.multiple_download_progress.setFormat("Download: %p%")
                self.disable_multiple_download_buttons()
                self.download_t1 = time.time()
                self.download_count = 0
                self.process_multiple_error = False
                self.process_multiple_file_exist = False
                
                try:
                    self.global_message.appendPlainText(self.cmd_to_msg(sublist[0], sublist[1]))
                    self.process_multiple.start(sublist[0], sublist[1])
                except (IOError, OSError) as err:
                    QMessageBox.question(self, 'Error', "%s"%err)
                    self.global_message.appendPlainText("=> Error: %s\n"%err)
                    self.enable_single_download_buttons()
            elif dm == get_concurrent_download_text():
                self.disable_multiple_parent_buttons()
                pc = ProcessController(self.multiple_download_job_list)
                #tp = ProcessTracker(pc, self.global_message) # modal
                tp = ProcessTracker(self, pc, self.global_message)
                pc.status_changed.connect(self.set_download_status)
                tp.status_changed.connect(self.set_download_button_status)
                #tp.exec_() #modal
                tp.show()
                
    
    def set_download_button_status(self, status):
        if status == _ydl_download_start:
            for k in range(self.youtube_path_tbl.rowCount()):
                self.youtube_path_tbl.item(k,0).setBackground(_ydl_color_white)
                self.youtube_path_tbl.item(k,2).setText("")
        elif status == _ydl_download_finish:
            self.enable_multiple_parent_buttons()
            
    def set_download_status(self, proc):
        key_num = int(proc.key.split(' ')[1])-1
        if proc.file_exist:
            self.youtube_path_tbl.item(key_num, 0).setBackground(_ydl_color_file_exist)
            self.youtube_path_tbl.item(key_num, 2).setText("Already exist")
        elif proc.error:
            self.youtube_path_tbl.item(key_num, 0).setBackground(_ydl_color_error)
            self.youtube_path_tbl.item(key_num, 2).setText("Error")
            self.global_message.appendPlainText(proc.status)
        else:
            self.youtube_path_tbl.item(key_num, 0).setBackground(_ydl_color_finished)
            self.youtube_path_tbl.item(key_num, 2).setText("Finished")
            
    def start_single_download(self):
        url = self.youtube_url.text()
        match = _valid_youtube_url.search(url)
        if not match:
            msg.message_box("Invalid URL", msg.message_error)
            return
        
        tab_text = self.youtube_tabs.tabText(self.youtube_tabs.currentIndex())
        
        arg_list = ['youtube-dl']
        self.single_download_step = 0
            
        if tab_text == get_single_tab_text():
        
            # format selected
            fmt = self.direct_format.text()
            id = -1
            cur_vcodec = None
            
            if self.direct_format_chk.isChecked() and fmt != "":
                arg_list.extend(['-f', fmt])
                
            elif self.choose_format_cmb.currentIndex() > 0:
                arg_list.extend(['-f', self.choose_format_cmb.currentText()])

            else:
                id = self.mood_av_button_group.checkedId()
                if id == 0: # audio only
                    audio_codec = self.single_download_audio_codec_cmb.currentText()
                    arg_list.extend([ _ydl_option_extract_audio,
                                      _ydl_option_audio_format,
                                      audio_codec])
                                    
                    if audio_codec != _ydl_best_audio_codec:
                        arg_list.extend([ _ydl_option_audio_quality, 
                                        self.single_download_audio_quality_cmb.currentText().split()[0]])
                
                elif id == 1: # video
                    cur_vcodec = self.single_download_video_codec_cmb.currentText()
                    if cur_vcodec != get_best_codec_name():
                        arg_list.extend([ _ydl_option_encode_video,
                                          cur_vcodec
                                        ])
            # Postprocess downloaded file w/ FFMpeg
            # Cut the video/audio 
            if self.single_download_ffmpeg_config.use_ffmpeg:
                if id==1 and (cur_vcodec == get_best_codec_name() or\
                              cur_vcodec == get_mkv_codec_name()) and\
                              self.single_download_ffmpeg_config.bypass_mkv:
                    # Bypassing mkv warning:
                    # Enforce the codec as mp4 because it's impossible to predict
                    # if the video will be put into MKV becuase of high quality
                    arg_list.extend(['-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]'])
                    
                arg_list.extend([ _ydl_option_choose_ffmpeg, 
                                  _ydl_option_ffmpeg_argument,
                                  self.single_download_ffmpeg_config.get_args()])
    
            if url.find('list') > -1:
                ret = msg.message_box("Do you want to download multiple videos?", msg.message_yesno)
                if ret == QMessageBox.No:
                    return
            
            self.process_single = QProcess(self)
            self.process_single.setReadChannel(QProcess.StandardOutput)
            self.process_single.setProcessChannelMode(QProcess.MergedChannels)
            self.process_single.finished.connect(self.single_download_finished)
            self.process_single.readyRead.connect(self.single_download_data_read)
            
            save_folder = os.path.join(self.youtube_save_path.text(), _ydl_option_output_filename)
            arg_list.extend([_ydl_option_output, save_folder, url.strip()])
            
            self.single_download_job_list=[[arg_list[0], arg_list[1:]]]
            
            sublist = self.single_download_job_list[0]
            del self.single_download_job_list[0]
            
            if self.single_download_timer.isActive():
                self.single_download_timer.stop()
            else:
                self.single_download_timer.start(100, self)
            
            self.single_download_progress.setTextVisible(True)
            self.single_download_progress.setFormat("Download: %p%")
            self.disable_single_download_buttons()
            self.download_t1 = time.time()
            self.process_single_error = False
            self.single_file_already_exist = False
            try:
                self.global_message.appendPlainText("%s\n"%self.cmd_to_msg(sublist[0], sublist[1]))
                self.process_single.start(sublist[0], sublist[1])
            except (IOError, OSError) as err:
                QMessageBox.question(self, 'Error', "%s"%err)
                self.global_message.appendPlainText("=> Error: %s\n"%err)
                self.enable_single_download_buttons()
    
    def cancel_single_download(self):
        if not self.process_single: return
        tab_text = self.youtube_tabs.tabText(self.youtube_tabs.currentIndex())
        self.global_message.appendPlainText("=> Cancel single download")
        if tab_text == get_single_tab_text():
            self.process_single.kill()
            self.single_download_timer.stop()
    
    def cmd_to_msg(self, cmd, arg=""):
        if isinstance(cmd, (list,)): msg1 = ' '.join(cmd)
        elif isinstance(cmd, (str,)): msg1 = cmd
        else: msg1 = "Invalid cmd type: %s"%type(cmd)
        
        if isinstance(arg, (list,)): msg2 = ' '.join(arg)
        elif isinstance(arg, (str,)): msg2 = arg
        else: msg2 = "Invalid arg type: %s"%type(arg)
        
        return "=> %s %s"%(msg1, msg2)    
    
def main():
    app = QApplication(sys.argv)

    # --- PyQt4 Only
    #app.setStyle(QStyleFactory.create(u'Motif'))
    #app.setStyle(QStyleFactory.create(u'CDE'))
    #app.setStyle(QStyleFactory.create(u'Plastique'))
    #app.setStyle(QStyleFactory.create(u'Cleanlooks'))
    # --- PyQt4 Only
    
    app.setStyle(QStyleFactory.create("Fusion"))
    ydl= QYoutubeDownloader()
    sys.exit(app.exec_())
    
if __name__ == '__main__':
    main()    

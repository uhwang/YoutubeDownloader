'''

    06/02/2022  FFMpeg     => self.process.setReadChannel(QtCore.QProcess.StandardError)
                Youtube-dl => self.process.setReadChannel(QtCore.QProcess.StandardOutput) 
                Download a single video from youtube
    06/03/2022  Ver 0.1
    
'''
import re, sys, os, subprocess
from PyQt4 import QtCore, QtGui
import time

import icon_encode_delete
import icon_encode_delete_all
import icon_encode_folder_open
import icon_encode_trash

import icon_request_format
import icon_download
import icon_cancel
import icon_edit
import icon_add_row
import icon_undo
import icon_setting
import icon_txt
import icon_json
import json
import msg

_youtube_tab_text = [ 
    "Single",
    "Multiple",
    "Setting"
]

# https://stackoverflow.com/questions/28735459/how-to-validate-youtube-url-in-client-side-in-text-box
_valid_youtube_url = re.compile("^(?:https?:\/\/)?(?:m\.|www\.)?(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=))((\w|-){11})(?:\S+)?$")

_ydl_option_video_list = "--flat-playlist"
_ydl_option_skip_download = "--skip-download"
_ydl_option_extract_audio = "--extract-audio"
_ydl_option_audio_format = "--audio-format"
_ydl_option_encode_video = "--recode-video"
_ydl_option_audio_quality = "--audio-quality"
_ydl_option_output = "-o"
_ydl_option_output_filename = "%(title)s-%(id)s.%(ext)s"
_ydl_const_error = "ERROR"
_ydl_const_exist = "already been downloaded"
_ydl_const_exist_text = "Already exist"
_ydl_const_filename = "Destination:"

_find_format = re.compile("\w+", re.MULTILINE )
_find_size = lambda x : x[x.rfind(' '):]
_find_percent = re.compile("\d+.\d+\%", re.MULTILINE )
_find_ydl_error = lambda x: x.strip() if x.find("ERROR:") >= 0 else None
_file_exist = lambda x: True if x.find(_ydl_const_exist) >= 0 else False
_find_filename = lambda x: x.split(_ydl_const_filename)[1].strip() if x.find(_ydl_const_filename) >= 0 else None

_exception_msg = lambda e : "=> {0} : {1}".format(type(e).__name__, str(e))

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
    "None",
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

_ydl_format_none = "N/A"

_ydl_audio_quality = [ str(x) for x in range(10)]

#https://arcpy.wordpress.com/2012/04/20/146/    
def hms_string(sec_elapsed):
    h = int(sec_elapsed / (60 * 60))
    m = int((sec_elapsed % (60 * 60)) / 60)
    s = sec_elapsed % 60.
    return "{}:{:>02}:{:>05.2f}".format(h, m, s)

def get_single_tab_text() : return _youtube_tab_text[0]
def get_multiple_tab_text() : return _youtube_tab_text[1]
def get_youtubedl_setting_tab_text() : return _youtube_tab_text[2]
def get_sequential_download_text() : return _ydl_multiple_download_method[0]
def get_concurrent_download_text() : return _ydl_multiple_download_method[1]
def get_current_tab_text(tab) : tab.tabText(tab.currentIndex())

def get_video_count_from_youtube_list(url):
    if url.find('list') < 0: 
        return

    cmd=['youtube-dl',  _ydl_option_video_list, url]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
    output = proc.communicate()[0]
    output = output.decode('utf-8')

    match = re.search("\d+ videos", output, re.MULTILINE)
    if match:
        return int(match.group(0).split(' ')[0])
    return None

#print(get_video_count_from_youtube_list("https://youtu.be/qny-ChWw3a0?list=PLrqHrGoMJdTR_P8p95DY1RA8_gD4XEOmI"))

def get_youtube_formats(url, skip_comment=3):
    cmd=['youtube-dl',  '-F', url]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
    output = proc.communicate()[0]
    
    #print(output)
    # fail to get formats 
    #if output.returncode:
    #    print("failed to get youtube video/audio formats")
    #    return None
    
    # http:#stackoverflow.com/questions/606191/convert-bytes-to-a-python-string
    output = output.decode('utf-8')
    output = output.split('\n')
    formats = output[skip_comment:]
    del proc
    
    return formats

def get_youtube_format_from_formats(format):

    e = _find_format.findall(format)
    size = _find_size(format)
    
    if len(e) < 1: return None
    
    if format.find('audio') > -1:
        return [e[0], e[1], e[2], e[5], size]
    else:
        return [e[0], e[1], e[2], e[4], size]
  
def fetch_youtube_format_from_url(url, tbl):
    
        if not _valid_youtube_url.search(url):
            msg.message_box("Invalid URL", msg.message_error)
            return

        if url == '':
            return
        
        formats = get_youtube_formats(url)
        frm = ["None"]
        
        for i, f in enumerate(formats):
            info = get_youtube_format_from_formats(f)
            if info == None: break
            tbl.insertRow(i)
            tbl.setItem(i, 0, QtGui.QTableWidgetItem(info[0]))
            tbl.setItem(i, 1, QtGui.QTableWidgetItem(info[1]))
            tbl.setItem(i, 2, QtGui.QTableWidgetItem(info[2]))
            tbl.setItem(i, 3, QtGui.QTableWidgetItem(info[3]))
            tbl.setItem(i, 4, QtGui.QTableWidgetItem(info[4]))
            frm.append(info[0])
        return frm
  
class QYoutubeDownloadFormatDlg(QtGui.QDialog):
    def __init__(self, url_table):
        super(QYoutubeDownloadFormatDlg, self).__init__()
        self.initUI(url_table)
        
    def initUI(self, url_table):
        self.format_unsable = False
        self.url_table = url_table
        layout = QtGui.QFormLayout()
        url_layout = QtGui.QHBoxLayout()
        url_layout.addWidget(QtGui.QLabel("URL #"))
        self.url_cmb = QtGui.QComboBox()
        self.url_cmb.addItems([str(x) for x in range(url_table.rowCount())])
        url_layout.addWidget(self.url_cmb)
        
        self.youtube_format_tbl = QtGui.QTableWidget()
        self.youtube_format_tbl.verticalHeader().hide()
        self.youtube_format_tbl.setColumnCount(5)
        self.youtube_format_tbl.setHorizontalHeaderItem(0, QtGui.QTableWidgetItem("Code"))
        self.youtube_format_tbl.setHorizontalHeaderItem(1, QtGui.QTableWidgetItem("Ext"))
        self.youtube_format_tbl.setHorizontalHeaderItem(2, QtGui.QTableWidgetItem("Res"))
        self.youtube_format_tbl.setHorizontalHeaderItem(3, QtGui.QTableWidgetItem("Bit"))
        self.youtube_format_tbl.setHorizontalHeaderItem(4, QtGui.QTableWidgetItem("Size"))

        header = self.youtube_format_tbl.horizontalHeader()
        header.setResizeMode(0, QtGui.QHeaderView.ResizeToContents)
        header.setResizeMode(1, QtGui.QHeaderView.ResizeToContents)
        header.setResizeMode(2, QtGui.QHeaderView.ResizeToContents)        
        header.setResizeMode(3, QtGui.QHeaderView.ResizeToContents)
        header.setResizeMode(4, QtGui.QHeaderView.ResizeToContents)        

        ans_layout = QtGui.QGridLayout()
        self.fetch_youtube_format_btn = QtGui.QPushButton('Fetch : Format Retrieve')
        #self.fetch_youtube_format_btn = QtGui.QPushButton('', self)
        #self.fetch_youtube_format_btn.setIcon(QtGui.QIcon(QtGui.QPixmap(icon_request_format.table)))
        #self.fetch_youtube_format_btn.setIconSize(QtCore.QSize(16,16))
        self.connect(self.fetch_youtube_format_btn, QtCore.SIGNAL('clicked()'), self.fetch_youtube_format)
        self.no_format = QtGui.QPushButton("N/A : Not Use Fromat")
        self.connect(self.no_format, QtCore.SIGNAL('clicked()'), self.not_use_format)
        self.ok = QtGui.QPushButton('OK')
        self.cancel = QtGui.QPushButton('CANCEL')
        self.ok.clicked.connect(self.accept)
        self.cancel.clicked.connect(self.reject)
        
        ans_layout.addWidget(self.fetch_youtube_format_btn)
        ans_layout.addWidget(self.no_format)
        ans_layout.addWidget(self.cancel)
        ans_layout.addWidget(self.ok)
        ans_layout.setContentsMargins(0,0,0,0)
        ans_layout.setSpacing(5)
        
        layout.addRow(url_layout)
        layout.addWidget(self.youtube_format_tbl)
        layout.addRow(ans_layout)
        
        self.setLayout(layout)
        
    def not_use_format(self):
        self.format_unsable = True
        self.accept()
        
    def fetch_youtube_format(self):
        url = self.url_table.item(self.url_cmb.currentIndex(),0).text()
        fetch_youtube_format_from_url(url, self.youtube_format_tbl)
        
    def get_format(self):
        yft = self.youtube_format_tbl
        row = yft.currentRow()
        return yft.item(row, 0).text() if row > 0 else _ydl_format_none
    
class QYoutubeDownloader(QtGui.QWidget):
    def __init__(self):
        super(QYoutubeDownloader, self).__init__()
        self.initUI()
        
    def initUI(self):
        layout = QtGui.QFormLayout()
        
        grid = QtGui.QGridLayout()
        grid.addWidget(QtGui.QLabel("Folder"), 0,0)
        self.youtube_save_path = QtGui.QLineEdit()
        self.youtube_save_path.setText(os.getcwd())  
        
        self.youtube_save_path_btn = QtGui.QPushButton()
        self.youtube_save_path_btn.setIcon(QtGui.QIcon(QtGui.QPixmap(icon_encode_folder_open.table)))
        self.youtube_save_path_btn.setIconSize(QtCore.QSize(16,16))
        self.connect(self.youtube_save_path_btn, QtCore.SIGNAL('clicked()'), self.get_new_youtube_download_path)
        grid.addWidget(self.youtube_save_path, 0, 1)
        grid.addWidget(self.youtube_save_path_btn, 0, 2)

        self.youtube_tabs = QtGui.QTabWidget()
        policy = self.youtube_tabs.sizePolicy()
        self.youtube_tabs.setSizePolicy(policy)
        self.youtube_tabs.setEnabled(True)
        self.youtube_tabs.setTabPosition(QtGui.QTabWidget.North)
        self.youtube_tabs.setObjectName('Youtube List')
    
        self.single_video_tab   = QtGui.QWidget()
        self.multiple_video_tab = QtGui.QWidget()
        self.youtubedl_setting_tab = QtGui.QWidget()
        
        self.youtube_tabs.addTab(self.single_video_tab, get_single_tab_text())
        self.youtube_tabs.addTab(self.multiple_video_tab, get_multiple_tab_text())
        self.youtube_tabs.addTab(self.youtubedl_setting_tab, get_youtubedl_setting_tab_text())
        self.youtube_tabs.currentChanged.connect(self.youtube_video_tab_changed)
        self.single_video_tab_UI()
        self.multiple_video_tab_UI()
        
        self.time_font = QtGui.QFont("Courier",11,True)
        #self.single_download_timer = QtCore.QTimer() 
        self.single_download_timer = QtCore.QBasicTimer()
        #self.multiple_download_timer = QtCore.QTimer()
        self.multiple_download_timer = QtCore.QBasicTimer()
        
        self.process_single = None
        self.process_multiple = None

        layout.addRow(grid)
        layout.addRow(self.youtube_tabs)
        self.setLayout(layout)
        self.setWindowTitle("Youtube")
        self.show()
        
    def get_new_youtube_download_path(self):
        startingDir = os.getcwd() 
        path = QtGui.QFileDialog.getExistingDirectory(None, 'Save folder', startingDir, 
        QtGui.QFileDialog.ShowDirsOnly)
        if not path: return
        self.youtube_save_path.setText(path)
        #os.chdir(path)    
        
    def youtube_video_tab_changed(self):
        pass
        
    def single_video_tab_UI(self):
        # single video download
        layout = QtGui.QFormLayout()
        grid = QtGui.QGridLayout()
        grid.addWidget(QtGui.QLabel("URL"), 1,0)
        self.youtube_url = QtGui.QLineEdit()
        #self.youtube_url.setText("Youtube URL")
        grid.addWidget(self.youtube_url, 1, 1)
        
        self.youtube_format_tbl = QtGui.QTableWidget()
        self.youtube_format_tbl.verticalHeader().hide()
        self.youtube_format_tbl.setColumnCount(5)
        self.youtube_format_tbl.setHorizontalHeaderItem(0, QtGui.QTableWidgetItem("Code"))
        self.youtube_format_tbl.setHorizontalHeaderItem(1, QtGui.QTableWidgetItem("Ext"))
        self.youtube_format_tbl.setHorizontalHeaderItem(2, QtGui.QTableWidgetItem("Res"))
        self.youtube_format_tbl.setHorizontalHeaderItem(3, QtGui.QTableWidgetItem("Bit"))
        self.youtube_format_tbl.setHorizontalHeaderItem(4, QtGui.QTableWidgetItem("Size"))

        header = self.youtube_format_tbl.horizontalHeader()
        header.setResizeMode(0, QtGui.QHeaderView.ResizeToContents)
        header.setResizeMode(1, QtGui.QHeaderView.ResizeToContents)
        header.setResizeMode(2, QtGui.QHeaderView.ResizeToContents)        
        header.setResizeMode(3, QtGui.QHeaderView.ResizeToContents)
        header.setResizeMode(4, QtGui.QHeaderView.ResizeToContents)
        
        grid_btn = QtGui.QGridLayout()
        self.fetch_youtube_format_btn = QtGui.QPushButton('', self)
        self.fetch_youtube_format_btn.setIcon(QtGui.QIcon(QtGui.QPixmap(icon_request_format.table)))
        self.fetch_youtube_format_btn.setIconSize(QtCore.QSize(16,16))
        self.connect(self.fetch_youtube_format_btn, QtCore.SIGNAL('clicked()'), self.fetch_youtube_format)
  
        self.delete_btn = QtGui.QPushButton('', self)
        self.delete_btn.setIcon(QtGui.QIcon(QtGui.QPixmap(icon_encode_delete.table)))
        self.delete_btn.setIconSize(QtCore.QSize(16,16))
        self.connect(self.delete_btn, QtCore.SIGNAL('clicked()'), self.delete_item)
        
        self.delete_all_btn = QtGui.QPushButton('', self)
        self.delete_all_btn.setIcon(QtGui.QIcon(QtGui.QPixmap(icon_encode_trash.table)))
        self.delete_all_btn.setIconSize(QtCore.QSize(16,16))
        self.connect(self.delete_all_btn, QtCore.SIGNAL('clicked()'), self.delete_all_item)

        grid_btn.addWidget(self.fetch_youtube_format_btn, 0, 0)
        grid_btn.addWidget(self.delete_btn, 0, 1)
        grid_btn.addWidget(self.delete_all_btn, 0, 2)

        self.single_download_audio_codec_cmb = QtGui.QComboBox()
        self.single_download_audio_codec_cmb.addItems(_ydl_audio_codec)
        
        self.single_download_audio_quality_cmb = QtGui.QComboBox()
        self.single_download_audio_quality_cmb.addItems(_ydl_audio_quality)
        
        self.single_download_video_codec_cmb = QtGui.QComboBox()
        self.single_download_video_codec_cmb.addItems(_ydl_video_codec)
        
        grid_btn.addWidget(self.single_download_audio_codec_cmb, 2,0)
        grid_btn.addWidget(self.single_download_audio_quality_cmb, 2,1)
        grid_btn.addWidget(self.single_download_video_codec_cmb, 2,2)
        
        # default audio quality for ffmpeg is 5
        self.single_download_audio_quality_cmb.setCurrentIndex(5)
        
        self.single_download_progress = QtGui.QProgressBar(self)
        grid_btn.addWidget(self.single_download_progress, 3,0, 1, 3)
        
        #av_group = QtGui.QGroupBox()
        moods = [QtGui.QRadioButton("A Only"), QtGui.QRadioButton("Video")]
        # Set a radio button to be checked by default
        moods[1].setChecked(True)   

        button_layout = QtGui.QHBoxLayout()
        # Create a button group for radio buttons: Audio / video
        self.mood_av_button_group = QtGui.QButtonGroup()
        
        for i in range(len(moods)):
            # Add each radio button to the button layout
            button_layout.addWidget(moods[i])
            # Add each radio button to the button group & give it an ID of i
            self.mood_av_button_group.addButton(moods[i], i)
            # Connect each radio button to a method to run when it's clicked
            self.connect(moods[i], QtCore.SIGNAL("clicked()"), self.single_download_AV_codec_clicked)

        self.single_download_AV_codec_clicked()

        grid_btn.addLayout(button_layout, 1, 0, 1, 2)

        self.choose_format_cmb = QtGui.QComboBox()
        grid_btn.addWidget(self.choose_format_cmb, 1,2)
        grid_btn.setContentsMargins(0,0,0,0)
        grid_btn.setSpacing(5)
        
        run_option = QtGui.QHBoxLayout()
        self.start_single_download_btn = QtGui.QPushButton()
        self.start_single_download_btn.setIcon(QtGui.QIcon(QtGui.QPixmap(icon_download.table)))
        self.start_single_download_btn.setIconSize(QtCore.QSize(32,32))
        self.connect(self.start_single_download_btn, QtCore.SIGNAL('clicked()'), self.start_single_download)
        
        self.cancel_single_download_btn = QtGui.QPushButton()
        self.cancel_single_download_btn.setIcon(QtGui.QIcon(QtGui.QPixmap(icon_cancel.table)))
        self.cancel_single_download_btn.setIconSize(QtCore.QSize(32,32))
        self.connect(self.cancel_single_download_btn, QtCore.SIGNAL('clicked()'), self.cancel_single_download)
        run_option.addWidget(self.start_single_download_btn)
        run_option.addWidget(self.cancel_single_download_btn)
        
        layout.addRow(grid)
        layout.addRow(self.youtube_format_tbl)
        layout.addRow(grid_btn)
        layout.addRow(run_option)
        
        self.single_video_tab.setLayout(layout)
        
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
        
    def delete_all_item(self):
        table = self.get_current_youtube_table()
        
        for i in reversed(range(table.rowCount())):
            table.removeRow(i)
        table.setRowCount(0)
        
        self.choose_format_cmb.clear()
        
    def delete_item(self):
        table = self.get_current_youtube_table()
        row = table.currentRow()
        row_count = table.rowCount()
        
        if row_count == 0: return
        
        if row_count == 1: self.delete_all_item()
        else:
        #if row_count > 1:
            column = table.currentColumn();
            for i in range(table.columnCount()):
                table.setItem(row,i,table.takeItem(row+1,i))
                table.setCurrentCell(row,column)
            table.removeRow(row+1)
            table.setRowCount(row_count-1)
            
        if table == self.youtube_format_tbl:
            self.choose_format_cmb.removeItem(row+1)
        
    def multiple_video_tab_UI(self):
        
        layout = QtGui.QFormLayout()
        
        self.youtube_path_tbl = QtGui.QTableWidget()
        #self.youtube_path_tbl.verticalHeader().hide()
        self.youtube_path_tbl.setColumnCount(3)
        self.youtube_path_tbl.setHorizontalHeaderItem(0, QtGui.QTableWidgetItem("URL"))
        self.youtube_path_tbl.setHorizontalHeaderItem(1, QtGui.QTableWidgetItem("Description"))
        self.youtube_path_tbl.setHorizontalHeaderItem(2, QtGui.QTableWidgetItem("Status"))
        #self.youtube_path_tbl.setHorizontalHeaderItem(2, QtGui.QTableWidgetItem("End"))

        header = self.youtube_path_tbl.horizontalHeader()
        #header.setResizeMode(0, QtGui.QHeaderView.ResizeToContents)
        #header.setResizeMode(1, QtGui.QHeaderView.ResizeToContents)
        #header.setResizeMode(2, QtGui.QHeaderView.ResizeToContents)        
        
        grid_btn = QtGui.QGridLayout()
        
        self.load_json_btn = QtGui.QPushButton('', self)
        self.load_json_btn.setIcon(QtGui.QIcon(QtGui.QPixmap(icon_json.table)))
        self.load_json_btn.setIconSize(QtCore.QSize(16,16))
        self.connect(self.load_json_btn, QtCore.SIGNAL('clicked()'), self.load_json)
        
        self.load_text_btn = QtGui.QPushButton('', self)
        self.load_text_btn.setIcon(QtGui.QIcon(QtGui.QPixmap(icon_txt.table)))
        self.load_text_btn.setIconSize(QtCore.QSize(16,16))
        self.connect(self.load_text_btn, QtCore.SIGNAL('clicked()'), self.load_text)

        self.global_download_format_btn = QtGui.QPushButton('Fmt: {}'.format(_ydl_format_none), self)
        self.connect(self.global_download_format_btn, QtCore.SIGNAL('clicked()'), self.choose_global_download_format)

        grid_btn.addWidget(self.load_json_btn, 1, 0)
        grid_btn.addWidget(self.load_text_btn, 1, 1)
        grid_btn.addWidget(self.global_download_format_btn, 1, 2)
        
        self.add_url_btn = QtGui.QPushButton('', self)
        self.add_url_btn.setIcon(QtGui.QIcon(QtGui.QPixmap(icon_add_row.table)))
        self.add_url_btn.setIconSize(QtCore.QSize(16,16))
        self.connect(self.add_url_btn, QtCore.SIGNAL('clicked()'), self.add_url)
        
        self.delete_btn = QtGui.QPushButton('', self)
        self.delete_btn.setIcon(QtGui.QIcon(QtGui.QPixmap(icon_encode_delete.table)))
        self.delete_btn.setIconSize(QtCore.QSize(16,16))
        self.connect(self.delete_btn, QtCore.SIGNAL('clicked()'), self.delete_item)
        
        self.delete_all_btn = QtGui.QPushButton('', self)
        self.delete_all_btn.setIcon(QtGui.QIcon(QtGui.QPixmap(icon_encode_trash.table)))
        self.delete_all_btn.setIconSize(QtCore.QSize(16,16))
        self.connect(self.delete_all_btn, QtCore.SIGNAL('clicked()'), self.delete_all_item)

        grid_btn.addWidget(self.add_url_btn, 0, 0)
        grid_btn.addWidget(self.delete_btn, 0, 1)
        grid_btn.addWidget(self.delete_all_btn, 0, 2)
        
        self.multiple_download_audio_codec_cmb = QtGui.QComboBox()
        self.multiple_download_audio_codec_cmb.addItems(_ydl_audio_codec)
        
        self.multiple_download_audio_quality_cmb = QtGui.QComboBox()
        self.multiple_download_audio_quality_cmb.addItems(_ydl_audio_quality)
        
        self.multiple_download_video_codec_cmb = QtGui.QComboBox()
        self.multiple_download_video_codec_cmb.addItems(_ydl_video_codec)
        
        grid_btn.addWidget(self.multiple_download_audio_codec_cmb, 3,0)
        grid_btn.addWidget(self.multiple_download_audio_quality_cmb, 3,1)
        grid_btn.addWidget(self.multiple_download_video_codec_cmb, 3,2)
        
        # default audio quality for ffmpeg is 5
        self.multiple_download_audio_quality_cmb.setCurrentIndex(5)
        
        #av_group = QtGui.QGroupBox()
        moods = [QtGui.QRadioButton("A Only"), QtGui.QRadioButton("Video")]
        # Set a radio button to be checked by default
        moods[1].setChecked(True)   

        button_layout = QtGui.QHBoxLayout()
        # Create a button group for radio buttons: Audio / video
        self.multiple_mood_AV_button_group = QtGui.QButtonGroup()
        
        for i in range(len(moods)):
            # Add each radio button to the button layout
            button_layout.addWidget(moods[i])
            # Add each radio button to the button group & give it an ID of i
            self.multiple_mood_AV_button_group.addButton(moods[i], i)
            # Connect each radio button to a method to run when it's clicked
            self.connect(moods[i], QtCore.SIGNAL("clicked()"), self.multiple_download_AV_codec_clicked)

        self.multiple_download_AV_codec_clicked()
        grid_btn.addLayout(button_layout, 2, 0, 1, 2)

        self.multiple_download_progress = QtGui.QProgressBar(self)
        grid_btn.addWidget(self.multiple_download_progress, 4, 0, 1, 3)

        grid_btn.setContentsMargins(0,0,0,0)
        grid_btn.setSpacing(5)
        
        self.multiple_download_method = QtGui.QComboBox()
        self.multiple_download_method.addItems(_ydl_multiple_download_method)
        self.multiple_download_method.setFixedWidth(75)
        grid_btn.addWidget(self.multiple_download_method, 2, 2)
        
        
        run_option = QtGui.QHBoxLayout()
        self.start_multiple_download_btn = QtGui.QPushButton()
        self.start_multiple_download_btn.setIcon(QtGui.QIcon(QtGui.QPixmap(icon_download.table)))
        self.start_multiple_download_btn.setIconSize(QtCore.QSize(32,32))
        self.connect(self.start_multiple_download_btn, QtCore.SIGNAL('clicked()'), self.start_multiple_download)
        
        self.cancel_multiple_download_btn = QtGui.QPushButton()
        self.cancel_multiple_download_btn.setIcon(QtGui.QIcon(QtGui.QPixmap(icon_cancel.table)))
        self.cancel_multiple_download_btn.setIconSize(QtCore.QSize(32,32))
        self.connect(self.cancel_multiple_download_btn, QtCore.SIGNAL('clicked()'), self.cancel_multiple_download)
        run_option.addWidget(self.start_multiple_download_btn)
        run_option.addWidget(self.cancel_multiple_download_btn)
        
        layout.addRow(self.youtube_path_tbl)
        layout.addRow(grid_btn)
        layout.addRow(run_option)
        
        self.multiple_video_tab.setLayout(layout)
        
    def load_json(self):
        file = QtGui.QFileDialog.getOpenFileName(self, "Load JSON", 
                directory=self.youtube_save_path.text(), 
                filter="Json (*.json );;All files (*.*)")
        
        if file: 
            path, fname = os.path.split(file)
            
            try:
                with open(file) as f:
                    videos = json.load(f)["videos"]
                    cur_row = self.youtube_path_tbl.rowCount()
                    for k, v in enumerate(videos):
                        self.youtube_path_tbl.insertRow(cur_row+k)
                        self.youtube_path_tbl.setItem(cur_row+k, 0, 
                            QtGui.QTableWidgetItem(v["url"]))
                        self.youtube_path_tbl.setItem(cur_row+k, 1, 
                            QtGui.QTableWidgetItem(v["desc"]))
                        self.youtube_path_tbl.setItem(cur_row+k, 2, 
                            QtGui.QTableWidgetItem(""))
            except Exception as e:
                msg.message_box(str(e), msg.message_error)
                return

    def load_text(self):
        pass

    def choose_global_download_format(self):
        nurl = self.youtube_path_tbl.rowCount()
        if nurl == 0: return
        format_dlg = QYoutubeDownloadFormatDlg(self.youtube_path_tbl)
        if format_dlg.exec_() == 1:
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
        self.youtube_path_tbl.setItem(cur_row, 0, QtGui.QTableWidgetItem(""))
        self.youtube_path_tbl.setItem(cur_row, 1, QtGui.QTableWidgetItem(""))
        self.youtube_path_tbl.setItem(cur_row, 2, QtGui.QTableWidgetItem(""))
        
    def fetch_youtube_format(self):
        frm = fetch_youtube_format_from_url(
            self.youtube_url.text(),
            self.youtube_format_tbl)
        self.choose_format_cmb.addItems(frm)
        
    def timerEvent(self, e):
        if self.process_single:
            self.single_download_progress.setValue(self.single_download_step)
            
        if self.process_multiple:
            self.multiple_download_progress.setValue(self.multiple_download_step)

    def single_download_data_read(self):
        try:
            #data = str(self.process_single.readAll(), 'utf-8')
            #data = str(self.process_single.readAll(), 'cp949') # Windows only
            data = str(self.process_single.readLine(), 'cp949') # Windows only
        except Exception as e:
            print(_exception_msg(e))
            return

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
            print("=> File Path: %s"%fpath)
            print("=> File Name: %s"%fname)
            #self.global_message.appendPlainText("=> %s"%fn)
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
            #data = str(self.process_single.readAll(), 'cp949') # Windows only
            data = str(self.process_single.readLine(), 'cp949') # Windows only            
        except Exception as e:
            print(_exception_msg(e), data)
            return
        
        if _find_ydl_error(data):
            self.process_multiple_error = True
            self.youtube_path_tbl.item(self.download_count, 0).setBackground(QtGui.QColor(247,79,83))
            self.youtube_path_tbl.item(self.download_count, 2).setText("Error")
            msg.message_box("URL: #%d\n%s"%(self.download_count,data), msg.message_error)
            return
            
        if _file_exist(data):
            self.youtube_path_tbl.item(self.download_count, 2).setText(_ydl_const_exist_text)
            return
            
        fn = _find_filename(data)
        if fn:
            fpath, fname = os.path.split(fn.strip())
            print("=> File Path: %s"%fpath)
            print("=> File Name: %s"%fname)
            #self.global_message.appendPlainText("=> Filename: %s"%fn)
            return

        match = _find_percent.search(data)
        if match:
            self.multiple_download_step = int(float(match.group(0)[:-1]))
            
    def multiple_download_finished(self):
        if self.process_multiple_error or len(self.multiple_download_job_list) == 0:
            self.enable_multiple_download_buttons()
            self.multiple_download_progress.setValue(100)
            self.multiple_download_timer.stop()
            self.process_multiple = None

            if not self.process_multiple_error:
                self.youtube_path_tbl.item(self.download_count, 0).setBackground(QtGui.QColor(230,213,89))
                self.youtube_path_tbl.item(self.download_count, 2).setText("Finished")
                self.global_message.appendPlainText("=> Miltiple Download Donw@")
                self.print_download_elasped()
            return
            
        self.youtube_path_tbl.item(self.download_count, 0).setBackground(QtGui.QColor(230,213,89))
        if self.youtube_path_tbl.item(self.download_count, 2).text() != _ydl_const_exist_text:
            self.youtube_path_tbl.item(self.download_count, 2).setText("Finished")
        self.download_count += 1
        
        sublist = self.multiple_download_job_list[0]
        del self.multiple_download_job_list[0]
        
        try:
            #self.global_message.appendPlainText(self.cmd_to_msg(sublist[0], sublist[1]))
            self.process_multiple.start(sublist[0], sublist[1])
        except (IOError, OSError) as err:
            QtGui.QMessageBox.question(self, 'Error', "%s"%err)
            self.delete_job_list()
            self.enable_multiple_download_buttons()
                        
    def enable_multiple_download_buttons(self):
        self.start_multiple_download_btn.setEnabled(True)
        
    def disable_multiple_download_buttons(self):
        self.start_multiple_download_btn.setEnabled(False)
        
    def print_download_elasped(self):
        download_t2 = time.time()
        elasped_time = hms_string(download_t2-self.download_t1)
        msg.message_box("Download Time: {}".format(elasped_time), msg.message_normal)
        
    def delete_job_list(self):
        self.single_download_job_list = []
        self.single_download_timer.stop()

    def enable_single_download_buttons(self):
        self.start_single_download_btn.setEnabled(True)
        
    def disable_single_download_buttons(self):
        self.start_single_download_btn.setEnabled(False)
        
    def cancel_multiple_download(self):
        if self.multiple_download_method.currentText() == get_sequential_download_text():
            self.process_multiple.kill()
            self.single_download_timer.stop()
        
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

            if id == 0: # audio only
                audio_codec = self.multiple_download_audio_codec_cmb.currentText()
                arg_list.extend([_ydl_option_extract_audio,
                                 _ydl_option_audio_format,
                                 audio_codec])
                                
                if audio_codec != _ydl_best_audio_codec:
                    arg_list.extend([_ydl_option_audio_quality, 
                                     self.multiple_download_audio_quality_cmb.currentText()])
            
            elif id == 1: # video
                if self.multiple_download_video_codec_cmb.currentIndex() > 0:
                    arg_list.extend([_ydl_option_encode_video,
                                     self.multiple_download_video_codec_cmb.currentText()])

            save_folder = os.path.join(self.youtube_save_path.text(), _ydl_option_output_filename)
            arg_list.extend([_ydl_option_output, save_folder])
 
            self.multiple_download_job_list = []
            arg_list.append(' ')
            for k in range(number_of_url):
                self.youtube_path_tbl.item(k,0).setBackground(QtGui.QColor(255,255,255))
                self.youtube_path_tbl.item(k,2).setText("")
                arg_list[-1] = self.youtube_path_tbl.item(k,0).text().strip()
                job = [arg_list[0], arg_list[1:]]
                self.multiple_download_job_list.append(job)
            '''    
            self.proc_list = []
            if self.multiple_download_method.currentText() == get_concurrent_download_text():
                for job in self.multiple_download_job_list:
                    cmd = []
                    cmd.append(job[0])
                    cmd.extend([arg for _, arg in enumerate(arg_list[1:])])
                    print(cmd)
                    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
                    self.proc_list.append(proc)
                    output = proc.communicate()[0]
                    print(output.decode('utf-8'))
            else:
            '''
            dm = self.multiple_download_method.currentText()
            
            if dm == get_concurrent_download_text() or dm == get_sequential_download_text():
                self.process_multiple = QtCore.QProcess(self)
                self.process_multiple.setReadChannel(QtCore.QProcess.StandardOutput)
                self.process_multiple.setProcessChannelMode(QtCore.QProcess.MergedChannels)
                QtCore.QObject.connect(self.process_multiple, QtCore.SIGNAL("finished(int)"), self.multiple_download_finished)
                QtCore.QObject.connect(self.process_multiple, QtCore.SIGNAL("readyRead()"), self.multiple_download_data_read)
            
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

                print(self.cmd_to_msg(sublist[0], sublist[1]))
                self.download_count = 0
                self.process_multiple_error = False
                
                try:
                    #self.global_message.appendPlainText(self.cmd_to_msg(sublist[0], sublist[1]))
                    self.process_multiple.start(sublist[0], sublist[1])
                except (IOError, OSError) as err:
                    QtGui.QMessageBox.question(self, 'Error', "%s"%err)
                    #self.global_message.appendPlainText("=> Error: %s"%err)
                    self.enable_single_download_buttons()
    
    
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
            if self.choose_format_cmb.currentIndex() > 0:
                arg_list.extend(['-f', self.choose_format_cmb.currentText()])
            
            id = self.mood_av_button_group.checkedId()
            
            if id == 0: # audio only
                audio_codec = self.single_download_audio_codec_cmb.currentText()
                arg_list.extend([_ydl_option_extract_audio,
                                 _ydl_option_audio_format,
                                 audio_codec])
                                  
                if audio_codec != _ydl_best_audio_codec:
                    arg_list.extend([_ydl_option_audio_quality, 
                                     self.single_download_audio_quality_cmb.currentText()])
            
            elif id == 1: # video
                if self.single_download_video_codec_cmb.currentIndex() > 0:
                    arg_list.extend([_ydl_option_encode_video,
                                     self.single_download_video_codec_cmb.currentText()])

            if url.find('list') > -1:
                ret = msg.message_box("Do you want to download multiple videos?", msg.message_warning)
                if ret is False:
                    return
                self.nvideo = get_video_count_from_youtube_list(url)

            else:
                self.nvideo = 1
            
            self.process_single = QtCore.QProcess(self)
            self.process_single.setReadChannel(QtCore.QProcess.StandardOutput)
            self.process_single.setProcessChannelMode(QtCore.QProcess.MergedChannels)
            QtCore.QObject.connect(self.process_single, QtCore.SIGNAL("finished(int)"), self.single_download_finished)
            QtCore.QObject.connect(self.process_single, QtCore.SIGNAL("readyRead()"), self.single_download_data_read)
            
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
            
            print(self.cmd_to_msg(sublist[0], sublist[1]))
            
            try:
                #self.global_message.appendPlainText(self.cmd_to_msg(sublist[0], sublist[1]))
                #self.single_download_started = True
                self.process_single.start(sublist[0], sublist[1])
            except (IOError, OSError) as err:
                QtGui.QMessageBox.question(self, 'Error', "%s"%err)
                #self.global_message.appendPlainText("=> Error: %s"%err)
                self.enable_single_download_buttons()
    
    def cancel_single_download(self):
        tab_text = self.youtube_tabs.tabText(self.youtube_tabs.currentIndex())
        
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
    app = QtGui.QApplication(sys.argv)
    QtGui.QApplication.setStyle(QtGui.QStyleFactory.create(u'Plastique'))
    lppt = QYoutubeDownloader()
    #lppt = QRun()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()	
    
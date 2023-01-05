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
    07/18/22    Create video urls from youtube url w/ list 
                
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
                              QGroupBox,
                              QTreeWidget,
                              QTreeWidgetItem)

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
import ydlproc
import util
import reutil
import ydlconst
import ydlcolor
import ydlconf
import funs
import dnlist

_clipboard = None

class Postprocess:
    def __init__(self):
        self.use_ffmpeg = False
        self.bypass_mkv = False
        self.use_time   = False
        self.t1         = "" # Start => 00:00:00:00 (HH:MM:SS:MS)
        self.t2         = "" # End   => 00:00:00:00 (HH:MM:SS:MS)
        self.atempo     = "1"
        self.filename   = ""
        
    def get_args(self):
        ff_args = list()
        if self.use_time:
            t1_sec = util.time_to_sec(self.t1)
            t2_sec = util.time_to_sec(self.t2)
            duration = t2_sec - t1_sec
            ff_args.extend([ydlconst._ydl_ffmpeg_start_time,
                            "%.2f"%t1_sec,
                            ydlconst._ydl_ffmpeg_duration,
                            "%.2f"%duration])
        #if self.atempo != ydlconst._ydl_get_default_atempo():
        #    ff_args.append(ydlconst._ydl_get_atempo_arg(self.atempo))
        ff_args.append(self.filename)
        return  ' '.join(ff_args)
        
    def __str__(self):
        return  "Use FFMpeg: %s\n"\
                "Bypass MKV: %s\n"\
                "Use Time  : %s\n"\
                "T1        : %s\n"\
                "T2        : %s\n"\
                "Atempo    : %s\n"%(
                self.use_ffmpeg, self.bypass_mkv, self.use_time, 
                self.t1, self.t2, self.atempo)

class PostprocessDlg(QDialog):
    def __init__(self, info):
        super(PostprocessDlg, self).__init__()
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
        self.timed_encoding_t1.setInputMask(ydlconst._ydl_ffmpeg_qt_time_mask)
        self.timed_encoding_t2.setInputMask(ydlconst._ydl_ffmpeg_qt_time_mask)
        font = QFont("Courier",8,True)
        fm = QFontMetrics(font)
        self.timed_encoding_t1.setFixedSize(fm.width(ydlconst._ydl_ffmpeg_qt_width_mask), fm.height())
        self.timed_encoding_t2.setFixedSize(fm.width(ydlconst._ydl_ffmpeg_qt_width_mask), fm.height())
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
        
        #atempo_layout = QHBoxLayout()
        #atempo_layout.addWidget(QLabel("Audio Speed"))
        #self.atempo_cmb = QComboBox()
        #self.atempo_cmb.addItems(ydlconst._ydl_ffmpeg_atempo_str)
        #self.atempo_cmb.setCurrentIndex(self.atempo_cmb.findText(info.atempo))
        #atempo_layout.addWidget(self.atempo_cmb)
        
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
        #layout.addRow(atempo_layout)
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
        
    def get_atempo(self):
        return self.atempo_cmb.currentText()

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
        self.scroll.setMaximumHeight(ydlconf.get_tacker_height())
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
            elasped_time = util.hms_string(end_time-self.start_time)
            self.msg.appendPlainText("=> Elasped time: {}\n=> Concurrent download Done!\n".format(elasped_time))
            self.enable_download_buttons()
            return
            
        for p in self.proc_ctrl.proc_pool.values():
            self.progress_bars[p.key].setValue(p.step)
            
    def set_download_status(self, proc):
        self.progress_bars[proc.key].setValue(proc.step)
        
    def start_download(self):
        self.status_changed.emit(ydlconst._ydl_download_start)
        
        for p_bar in self.progress_bars.values():
            p_bar.setValue(0)
            p_bar.setTextVisible(True)
            p_bar.setFormat("Download: %p%")
        self.disable_download_buttons()
        self.start_time = time.time()
        
        if self.timer.isActive():
            self.timer.stop()
        else:
            self.timer.start(ydlconf.get_concurrent_download_timer_interval(), self)
        
        try:
            self.proc_ctrl.start()
        except Exception as e:
            err_msg = "Error(ProcessTracker)\n... start_download\n...%s"%reutil._exception_msg(e)
            msg.message_box(err_msg, msg.message_error)
            self.msg.appendPlainText("=> %s\n"%err_msg)
            self.enable_download_buttons()        
            
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
        self.status_changed.emit(ydlconst._ydl_download_finish)
        
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
        util.delete_all_item(self.youtube_format_tbl, None)
        url = self.url_table.item(self.url_cmb.currentIndex(),0).text()
        if url.find("vimeo") > -1:
            msg.message_box("Doesn't work on Vimeo!", msg.message_warning)
            return
            
        util.fetch_youtube_format_from_url(url, self.youtube_format_tbl, self.msg)
        
    def get_format(self):
        fmt = self.direct_format.text()
        row = self.youtube_format_tbl.currentRow()
        return fmt if self.direct_format_chk.isChecked() and  fmt != ""\
                else self.youtube_format_tbl.item(row, 0).text()\
                if row >= 0 else ydlconst._ydl_format_none
                  
# ---------------------------------------------------------------------
#                  YOUTUBE DOWNLOADER
# ---------------------------------------------------------------------

class QYoutubeDownloader(QWidget):
    def __init__(self):
        super(QYoutubeDownloader, self).__init__()
        self.single_download_ffmpeg_config = Postprocess()
        ydlconf.load_config()
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
        self.encode_tab    = QWidget()
        self.message_tab    = QWidget()
        
        self.tabs.addTab(self.youtube_tab, funs.get_youtubetab_text())
        self.tabs.addTab(self.encode_tab, funs.get_encodetab_text())
        self.tabs.addTab(self.message_tab, funs.get_messagetab_text())
        
        self.youtube_download_tab_UI()
        self.message_tab_UI()
        self.global_message.appendPlainText(ydlconf.dump_config())
        
        tab_layout.addWidget(self.tabs)
        self.form_layout.addRow(tab_layout)
        self.setLayout(self.form_layout)
        self.setWindowTitle("YDL")
        self.setWindowIcon(QIcon(QPixmap(icon_youtube.table)))
        self.show()
    
    def encode_tab_UI(self):
        #import icon_arrow_down
        #import icon_arrow_up
        #import icon_append_url
        #import icon_copyvlist
        
        layout = QFormLayout()
        
        self.youtube_path_tbl = QTableWidget()
        self.youtube_path_tbl.setColumnCount(3)
        self.youtube_path_tbl.setHorizontalHeaderItem(0, QTableWidgetItem("URL"))
        self.youtube_path_tbl.setHorizontalHeaderItem(1, QTableWidgetItem("Description"))
        self.youtube_path_tbl.setHorizontalHeaderItem(2, QTableWidgetItem("Status"))

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
        font = QFont('monospace')
        font.setStyleHint(QFont.TypeWriter)
        self.global_message.setFont(font)
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
        self.create_vlist_tab = QWidget()
        self.setting_tab = QWidget()
        
        self.youtube_tabs.addTab(self.single_video_tab, funs.get_single_tab_text())
        self.youtube_tabs.addTab(self.multiple_video_tab, funs.get_multiple_tab_text())
        self.youtube_tabs.addTab(self.create_vlist_tab, funs.get_urllisttab_text())
        self.youtube_tabs.addTab(self.setting_tab, funs.get_youtubedl_setting_tab_text())
        self.youtube_tabs.currentChanged.connect(self.youtube_video_tab_changed)
        self.single_video_tab_UI()
        self.multiple_video_tab_UI()
        self.create_vlist_tab_UI()
        self.setting_tab_UI()
        
        self.time_font = QFont("Courier",11,True)
        self.single_download_timer = QBasicTimer()
        self.multiple_download_timer = QBasicTimer()
        
        self.process_single = None
        self.process_multiple = None

        layout.addRow(grid)
        layout.addRow(self.youtube_tabs)
        self.youtube_tab.setLayout(layout)
        
    def setting_tab_UI(self):
        import icon_apply
        import icon_undo
        import icon_dump_config
        
        # https://doc.qt.io/qtforpython/overviews/stylesheet-examples.html
        style = '''QTreeWidget::item:selected:active{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #6ea1f1, stop: 1 #567dbc);
                }
                QTreeView::item:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #e7effd, stop: 1 #cbdaf1);
                border: 1px solid #bfcde4;
                }
                '''
        layout = QFormLayout()
        self.config_tree = QTreeWidget()
        self.config_tree.setColumnCount(2)
        self.config_tree.setHeaderLabels(["Name", "Value"])
        self.config_tree.setStyleSheet(style)
        
        for key1, item1 in ydlconf._config.items():
            tree_item = QTreeWidgetItem(self.config_tree)
            tree_item.setText(0,key1)
            for key2, val in item1.items():
                sub_item = QTreeWidgetItem()
                sub_item.setText(0,key2)
                sub_item.setText(1,val)
                sub_item.setFlags(sub_item.flags()|Qt.ItemIsEditable)
                tree_item.addChild(sub_item)
        
        resp_lay = QHBoxLayout()

        self.apply_config_btn = QPushButton()
        self.apply_config_btn.setIcon(QIcon(QPixmap(icon_apply.table)))
        self.apply_config_btn.setIconSize(QSize(24,24))
        self.apply_config_btn.setToolTip("Apply current configure")
        self.apply_config_btn.clicked.connect(self.apply_config)

        self.undo_config_btn = QPushButton()
        self.undo_config_btn.setIcon(QIcon(QPixmap(icon_undo.table)))
        self.undo_config_btn.setIconSize(QSize(24,24))
        self.undo_config_btn.setToolTip("Set default value")
        self.undo_config_btn.clicked.connect(self.undo_config)
        
        self.save_config_btn = QPushButton()
        self.save_config_btn.setIcon(QIcon(QPixmap(icon_save.table)))
        self.save_config_btn.setIconSize(QSize(24,24))
        self.save_config_btn.setToolTip("Save configure")
        self.save_config_btn.clicked.connect(self.save_config)

        self.dump_config_btn = QPushButton()
        self.dump_config_btn.setIcon(QIcon(QPixmap(icon_dump_config.table)))
        self.dump_config_btn.setIconSize(QSize(24,24))
        self.dump_config_btn.setToolTip("Print configure")
        self.dump_config_btn.clicked.connect(self.dump_config)
        
        resp_lay.addWidget(self.apply_config_btn)
        resp_lay.addWidget(self.undo_config_btn)
        resp_lay.addWidget(self.save_config_btn)
        resp_lay.addWidget(self.dump_config_btn)
        
        layout.addWidget(self.config_tree)
        layout.addRow(resp_lay)
        
        self.setting_tab.setLayout(layout)
        
    def apply_config(self):

        for i in range(self.config_tree.topLevelItemCount()):
            item = self.config_tree.topLevelItem(i)
            name = item.text(0)
            nchild = item.childCount()
            for j in range(nchild):
                field = item.child(j).text(0)
                value = item.child(j).text(1)
                ydlconf._config[name][field] = value
        
    def undo_config(self):
        ydlconf.set_default_config()
        for i in range(self.config_tree.topLevelItemCount()):
            item = self.config_tree.topLevelItem(i)
            name = item.text(0)
            nchild = item.childCount()
            for j in range(nchild):
                field = item.child(j).text(0)
                item.child(j).setText(1, ydlconf._config[name][field])
        
    def dump_config(self):
        self.global_message.appendPlainText(ydlconf.dump_config())
        
    def save_config(self):
        ydlconf.save_config()
        
    def get_new_youtube_download_path(self):
        startingDir = os.getcwd() 
        path = QFileDialog.getExistingDirectory(None, 'Save folder', startingDir, 
        QFileDialog.ShowDirsOnly)
        if not path: return
        self.youtube_save_path.setText(path)
        #os.chdir(path)    
        
    def youtube_video_tab_changed(self):
        pass
        
    def create_vlist_tab_UI(self):
        import icon_startvlist
        import icon_stopvlist
        import icon_clear_url_input
        import icon_copy_url_input
        import icon_copyvlist
        import icon_restore
        import icon_clear_vlist_msg
        
        self.create_vlist = None
        self.vlist_copy = None
        
        layout = QFormLayout()

        grid = QGridLayout()
        grid.addWidget(QLabel("URL"), 1,0)
        self.video_url = QLineEdit()

        self.clear_url_btn = QPushButton('', self)
        self.clear_url_btn.setIcon(QIcon(QPixmap(icon_clear_url_input.table)))
        self.clear_url_btn.setIconSize(QSize(16,16))
        self.clear_url_btn.setToolTip("Clear url input")
        self.clear_url_btn.clicked.connect(partial(util.clear_url_input, self.video_url))
        
        self.copy_url_btn = QPushButton('', self)
        self.copy_url_btn.setIcon(QIcon(QPixmap(icon_copy_url_input.table)))
        self.copy_url_btn.setIconSize(QSize(16,16))
        self.copy_url_btn.setToolTip("Copy a url from clipboard")
        self.copy_url_btn.clicked.connect(partial(util.copy_url_input, self.video_url, _clipboard))
        
        grid.addWidget(self.video_url, 1, 1)
        grid.addWidget(self.clear_url_btn, 1, 2)
        grid.addWidget(self.copy_url_btn, 1, 3)
                
        self.vlist_message = QPlainTextEdit()

        save_lay = QHBoxLayout()
        #resp_lay.setContentsMargins(0,0,0,0)
        self.save_all_vlist_chk = QCheckBox("Save All")
        self.save_all_vlist_chk.stateChanged.connect(self.save_all_vlist_changed)
        self.video_list_range = QLineEdit()
        self.video_list_range.setFixedWidth(100)
        self.video_list_range.setToolTip("Ex: 1-10")

        save_lay.addWidget(self.save_all_vlist_chk)
        save_lay.addWidget(QLabel("Video Range"))
        save_lay.addWidget(self.video_list_range)
        
        ans_lay = QHBoxLayout()
        self.create_vlist_btn = QPushButton()
        self.create_vlist_btn.setIcon(QIcon(QPixmap(icon_startvlist.table)))
        self.create_vlist_btn.setIconSize(QSize(24,24))
        self.create_vlist_btn.clicked.connect(self.create_video_list)
        
        self.cancel_create_vlist_btn = QPushButton()
        self.cancel_create_vlist_btn.setIcon(QIcon(QPixmap(icon_stopvlist.table)))
        self.cancel_create_vlist_btn.setIconSize(QSize(24, 24))
        self.cancel_create_vlist_btn.clicked.connect(self.cancel_create_vlist)

        self.copy_vlist_btn = QPushButton('', self)
        self.copy_vlist_btn.setIcon(QIcon(QPixmap(icon_copyvlist.table)))
        self.copy_vlist_btn.setIconSize(QSize(24,24))
        self.copy_vlist_btn.setToolTip("Copy the video list")
        self.copy_vlist_btn.clicked.connect(self.copy_vlist)

        self.save_vlist_json_btn = QPushButton('', self)
        self.save_vlist_json_btn.setIcon(QIcon(QPixmap(icon_save.table)))
        self.save_vlist_json_btn.setIconSize(QSize(24,24))
        self.save_vlist_json_btn.setToolTip("Save the list of URLs as JSON format")
        self.save_vlist_json_btn.clicked.connect(self.save_vlist)

        self.restore_vlist_msg_btn = QPushButton('', self)
        self.restore_vlist_msg_btn.setIcon(QIcon(QPixmap(icon_restore.table)))
        self.restore_vlist_msg_btn.setIconSize(QSize(24,24))
        self.restore_vlist_msg_btn.setToolTip("Restore video list")
        self.restore_vlist_msg_btn.clicked.connect(self.restore_vlist_msg)
        
        self.clear_vlist_msg_btn = QPushButton('', self)
        self.clear_vlist_msg_btn.setIcon(QIcon(QPixmap(icon_trash_url.table)))
        self.clear_vlist_msg_btn.setIconSize(QSize(24,24))
        self.clear_vlist_msg_btn.setToolTip("Delete all messages")
        self.clear_vlist_msg_btn.clicked.connect(self.clear_vlist_msg)
        
        ans_lay.addWidget(self.create_vlist_btn)
        ans_lay.addWidget(self.cancel_create_vlist_btn)
        ans_lay.addWidget(self.copy_vlist_btn)
        ans_lay.addWidget(self.restore_vlist_msg_btn)
        ans_lay.addWidget(self.clear_vlist_msg_btn)
        ans_lay.addWidget(self.save_vlist_json_btn)

        self.save_all_vlist_chk.setChecked(True)
        
        layout.addRow(grid)
        layout.addWidget(self.vlist_message)
        layout.addRow(save_lay)
        layout.addRow(ans_lay)
        self.create_vlist_tab.setLayout(layout)
        
    def restore_vlist_msg(self):
        if self.create_vlist == None:
            return
            
        count = len(self.create_vlist._video_list)
        for k, u in enumerate(self.create_vlist._video_list):
            self.vlist_message.appendPlainText("... %d of %d : %s"%(k+1, count, u))
            
    def copy_vlist(self):
        try:
            self.vlist_copy, ncopy = self.create_vlist_jason()
        except Exception as e:
            err_msg = reutil._exception_msg(e)
            self.vlist_message.appendPlainText(err_msg)
            msg.message_box(err_msg, msg.message_error)    
            self.vlist_copy = None
            return
        msg.message_box("%d URLs copied!"%ncopy, msg.message_normal)
        
    def create_vlist_jason(self):
        if not self.create_vlist:
            raise RuntimeError("create_vlist_jason => vlist not yet created")
            
        count = self.create_vlist._video_count
        if count == 0: 
            raise RuntimeError("create_video_jason => no video list exist!")

        if self.save_all_vlist_chk.isChecked():
            v1 = 0
            v2 = count
        else:
            num_range = self.video_list_range.text()
            m = reutil._find_vlist_range.search(num_range)
            if not m:
                err_msg = "create_video_jason => invalid number range\n%s"%num_range
                self.vlist_message.appendPlainText(err_msg)
                raise RuntimeError(err_msg)
                
            v1 = int(m[1])-1
            v2 = int(m[2])
            if v1 < 0 or v2 > count:
                err_msg = "create_video_jason => Invalid number(%s)"%num_range
                self.vlist_message.appendPlainText(err_msg)
                msg.message_box(err_msg, msg.message_error)
                raise RuntimeError(err_msg)
                
        vlist_data = OrderedDict()
        v_list = list()
        
        for k in range(v1, v2):
            url = self.create_vlist._video_list[k]
            desc = "%d of %d"%(k+1, self.create_vlist._video_count)
            v_list.append({"desc": desc, "url": ydlconst._ydl_url_prefix+url})
        vlist_data["videos"] = v_list
        
        return vlist_data, v2-v1
            
    def clear_vlist_msg(self):
        self.vlist_message.clear()
        #self.vlist_copy = None
        
    def save_all_vlist_changed(self):
        if self.save_all_vlist_chk.isChecked():
            self.video_list_range.setEnabled(False)
        else:
            self.video_list_range.setEnabled(True)
            
    def get_create_vlist_status(self, status):
        self.vlist_message.appendPlainText(status)
            
    def create_video_list(self):
        url = self.video_url.text()
        
        if reutil._url_is_vimeo(url):
            msg.message_box("Invalid Youtube URL", msg.message_error)
            return
            
        self.create_vlist = dnlist.QCreateVideoListFromURL(url, self.vlist_message)
        self.create_vlist.status_changed.connect(self.get_create_vlist_status)
        self.create_vlist.create_video_list_from_youtube_url()
        
    def cancel_create_vlist(self):
        if self.create_vlist == None:
            return
            
        if not self.create_vlist.finished():
            res = msg.message_box("Still Running\nDo you want to quit?", msg.message_yesno)
            if res == QMessageBox.Yes:
                self.create_vlist.cancel()
                self.vlist_message.appendPlainText("... Job Canceled")
        
    def save_vlist(self):
        try:
            self.vlist_copy, ncopy = self.save_vlist_json()
        except Exception as e:
            err_msg = reutil._exception_msg(e)
            self.vlist_message.appendPlainText(err_msg)
            msg.message_box(err_msg, msg.message_error)    
            self.vlist_copy = None
            return
        msg.message_box("%d URLs copied!"%ncopy, msg.message_normal)
               
    def save_vlist_json(self):
        if not self.create_vlist:
            raise RuntimeError("save_vlist_json => vlist not yet created")
            
        count = self.create_vlist._video_count
        if count == 0: 
            raise RuntimeError("save_vlist_json => no video list exist!")
            
        data, _ = self.create_vlist_jason()
        if data == None:
            return
            
        json_export_file = 'ydl_url_list.json'
        json_save_path = os.path.join(self.youtube_save_path.text(), json_export_file)
        json_save_file = QFileDialog.getSaveFileName(None, 'Save File', json_save_path, 
                         'JSON files (*.json);;All files (*)')
        
        json_save_file = json_save_file[0] # PyQt5
        if json_save_file == '':
            return
        
        if json_save_file.find(".json") == -1:
            json_save_file += ".json"
        
        try:
            with open(json_save_file, 'w') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            err_msg = "Error(save_vlist_json)\n%s"%_exception_msg(e)
            self.global_message.appendPlainText("=> %s\n"%err_msg)
            msg.message_box(err_msg, msg.message_error)
            return
            
        self.global_message.appendPlainText("save_vlist_json\n... URL saved at %s"%json_save_file)
        msg.message_box("URL saved at %s"%json_save_file, msg.message_normal)
        
    def single_video_tab_UI(self):
        import icon_media_edit
        import icon_clear_url_input
        import icon_copy_url_input
        
        # single video download
        layout = QFormLayout()
        grid = QGridLayout()
        grid.addWidget(QLabel("URL"), 1,0)
        self.youtube_url = QLineEdit()

        self.clear_url_btn = QPushButton('', self)
        self.clear_url_btn.setIcon(QIcon(QPixmap(icon_clear_url_input.table)))
        self.clear_url_btn.setIconSize(QSize(16,16))
        self.clear_url_btn.setToolTip("Clear url input")
        self.clear_url_btn.clicked.connect(partial(util.clear_url_input, self.youtube_url))
        
        self.copy_url_btn = QPushButton('', self)
        self.copy_url_btn.setIcon(QIcon(QPixmap(icon_copy_url_input.table)))
        self.copy_url_btn.setIconSize(QSize(16,16))
        self.copy_url_btn.setToolTip("Copy a url from clipboard")
        self.copy_url_btn.clicked.connect(partial(util.copy_url_input, self.youtube_url, _clipboard))
        
        grid.addWidget(self.youtube_url, 1, 1)
        grid.addWidget(self.clear_url_btn, 1, 2)
        grid.addWidget(self.copy_url_btn, 1, 3)
        
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
        self.single_download_audio_codec_cmb.addItems(ydlconst._ydl_audio_codec)
        
        self.single_download_audio_quality_cmb = QComboBox()
        self.single_download_audio_quality_cmb.addItems(ydlconst._ydl_audio_quality)
        
        self.single_download_video_codec_cmb = QComboBox()
        self.single_download_video_codec_cmb.addItems(ydlconst._ydl_video_codec)
        
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
        
        self.delete_btn.clicked.connect(partial(util.delete_item, self.youtube_format_tbl, self.choose_format_cmb))
        self.delete_all_btn.clicked.connect(partial(util.delete_all_item, self.youtube_format_tbl, self.choose_format_cmb))

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
        dlg = PostprocessDlg(self.single_download_ffmpeg_config)
        res = dlg.exec_()
        
        if res == QDialog.Accepted:
            self.single_download_ffmpeg_config.use_ffmpeg = True
            self.single_download_ffmpeg_config.bypass_mkv = dlg.get_bypass()
            
            if self.single_download_ffmpeg_config.use_time:
                t1 = dlg.get_t1()
                t2 = dlg.get_t2()
                
                match1 = reutil._check_time.search(t1)
                match2 = reutil._check_time.search(t2)
        
                if not match1 or not match2:
                    msg.message_box("Invalid time format(start or end)!", msg.message_warning)
                    self.global_message.appendPlainText("Error(set_single_download_ffmpeg_config)\nT1 : %s\nT2 : %s\n"%(t1,t2))
                    return

                self.single_download_ffmpeg_config.t1 = t1
                self.single_download_ffmpeg_config.t2 = t2
            #self.single_download_ffmpeg_config.atempo = dlg.get_atempo()
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
        import icon_append_url
        import icon_copyvlist
        
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
        self.move_url_up_btn.clicked.connect(partial(util.move_item_up, self.youtube_path_tbl))

        self.move_url_down_btn = QPushButton('', self)
        self.move_url_down_btn.setIcon(QIcon(QPixmap(icon_arrow_down.table)))
        self.move_url_down_btn.setIconSize(QSize(24,24))
        self.move_url_down_btn.setToolTip("Move a URL down")
        self.move_url_down_btn.clicked.connect(partial(util.move_item_down, self.youtube_path_tbl))
        
        self.delete_btn = QPushButton('', self)
        self.delete_btn.setIcon(QIcon(QPixmap(icon_delete_url.table)))
        self.delete_btn.setIconSize(QSize(24,24))
        self.delete_btn.setToolTip("Delete a URL")
        self.delete_btn.clicked.connect(partial(util.delete_item, self.youtube_path_tbl, None))
        
        self.delete_all_btn = QPushButton('', self)
        self.delete_all_btn.setIcon(QIcon(QPixmap(icon_trash_url.table)))
        self.delete_all_btn.setIconSize(QSize(24,24))
        self.delete_all_btn.setToolTip("Delete All URLs")
        self.delete_all_btn.clicked.connect(partial(util.delete_all_item, self.youtube_path_tbl, None))

        grid_table_btn.addWidget(self.add_url_btn, 0, 0)
        grid_table_btn.addWidget(self.move_url_up_btn, 0, 1)
        grid_table_btn.addWidget(self.move_url_down_btn, 0, 2)
        grid_table_btn.addWidget(self.delete_btn, 0, 3)
        grid_table_btn.addWidget(self.delete_all_btn, 0, 4)

        self.load_json_btn = QPushButton('', self)
        self.load_json_btn.setIcon(QIcon(QPixmap(icon_json.table)))
        self.load_json_btn.setIconSize(QSize(24,24))
        self.load_json_btn.setToolTip("Load a list of URLs with JSON format")
        self.load_json_btn.clicked.connect(self.load_json)
        
        self.append_json_btn = QPushButton('', self)
        self.append_json_btn.setIcon(QIcon(QPixmap(icon_append_url.table)))
        self.append_json_btn.setIconSize(QSize(24,24))
        self.append_json_btn.setToolTip("Append a list of URLs")
        self.append_json_btn.clicked.connect(partial(self.load_json, True))
        
        self.paste_vlist_btn = QPushButton('', self)
        self.paste_vlist_btn.setIcon(QIcon(QPixmap(icon_copyvlist.table)))
        self.paste_vlist_btn.setIconSize(QSize(24,24))
        self.paste_vlist_btn.setToolTip("Paste the video list")
        self.paste_vlist_btn.clicked.connect(self.paste_vlist)
        
        self.save_json_btn = QPushButton('', self)
        self.save_json_btn.setIcon(QIcon(QPixmap(icon_save.table)))
        self.save_json_btn.setIconSize(QSize(24,24))
        self.save_json_btn.setToolTip("Save the list of URLs as JSON format")
        self.save_json_btn.clicked.connect(self.save_json)

        self.global_download_format_btn = QPushButton('Fmt: {}'.format(ydlconst._ydl_format_none), self)
        self.global_download_format_btn.clicked.connect(self.choose_global_download_format)

        grid_table_btn.addWidget(self.load_json_btn, 1, 0)
        grid_table_btn.addWidget(self.append_json_btn, 1, 1)
        grid_table_btn.addWidget(self.save_json_btn, 1, 2)
        grid_table_btn.addWidget(self.paste_vlist_btn, 1, 3)
        
        grid_option_btn = QGridLayout()
        
        self.multiple_download_audio_codec_cmb = QComboBox()
        self.multiple_download_audio_codec_cmb.addItems(ydlconst._ydl_audio_codec)
        
        self.multiple_download_audio_quality_cmb = QComboBox()
        self.multiple_download_audio_quality_cmb.addItems(ydlconst._ydl_audio_quality)
        
        self.multiple_download_video_codec_cmb = QComboBox()
        self.multiple_download_video_codec_cmb.addItems(ydlconst._ydl_video_codec)
        
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
        self.multiple_download_method.addItems(ydlconst._ydl_multiple_download_method)
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
        
    def paste_vlist(self):
        if self.vlist_copy == None:
            msg.message_box("Error: no video list exist!", msg.message_error)
            return

        cur_row = self.youtube_path_tbl.rowCount()
        
        if cur_row > 0:
            res = msg.message_box("Do you want to DELETE all current URLs?", msg.message_yesno)
            if res == QMessageBox.Yes:
                util.delete_all_item(self.youtube_path_tbl)
                cur_row = self.youtube_path_tbl.rowCount()
        
        videos = self.vlist_copy["videos"]

        for k, v in enumerate(videos):
            self.youtube_path_tbl.insertRow(cur_row+k)
            self.youtube_path_tbl.setItem(cur_row+k, 0, 
                QTableWidgetItem(v["url"]))
            self.youtube_path_tbl.setItem(cur_row+k, 1, 
                QTableWidgetItem(v["desc"]))
            self.youtube_path_tbl.setItem(cur_row+k, 2, 
                QTableWidgetItem(""))   
        
    def save_json(self):
        count = self.youtube_path_tbl.rowCount()
        if count == 0: return

        json_export_file = 'ydl_url_list.json'
        json_save_path = os.path.join(self.youtube_save_path.text(), json_export_file)
        json_save_file = QFileDialog.getSaveFileName(None, 'Save File', json_save_path, 
                         'JSON files (*.json);;All files (*)')
        
        json_save_file = json_save_file[0] # PyQt5
        if json_save_file == '':
            return
            
        data = OrderedDict()
        v_list = list()
        
        for k in range(count):
            url = self.youtube_path_tbl.item(k,0).text()
            desc = self.youtube_path_tbl.item(k,1).text()
            v_list.append({"desc": desc, "url": url})
        data["videos"] = v_list
            
        if json_save_file.find(".json") == -1:
            json_save_file += ".json"
        
        try:
            with open(json_save_file, 'w') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            err_msg = "Error(save_json)\n%s"%reutil._exception_msg(e)
            self.global_message.appendPlainText("=> %s\n"%err_msg)
            msg.message_box(err_msg, msg.message_error)
            return
            
        self.global_message.appendPlainText("URL saved at %s"%json_save_file)
        msg.message_box("URL saved at %s"%json_save_file, msg.message_normal)
            
    def load_json(self, append=False):
        file = QFileDialog.getOpenFileName(self, "Load JSON", 
                directory=self.youtube_save_path.text(), 
                filter="Json (*.json );;All files (*.*)")

        file = file[0] # uncomment this line for PyQt5
        
        if file: 
            path, fname = os.path.split(file)
            os.chdir(path)
            
            try:
                with open(file) as f:
                    videos = json.load(f)["videos"]
                    if append == False:
                        util.delete_all_item(self.youtube_path_tbl)
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
                err_msg = "Error(load_json)\n%s"%reutil._exception_msg(e)
                self.global_message.appendPlainText("=> %s\n"%err_msg)
                msg.message_box(err_msg, msg.message_error)
        
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
        util.delete_all_item(self.youtube_format_tbl, self.choose_format_cmb)
        url = self.youtube_url.text()
        
        if reutil._url_is_vimeo(url):
            msg.message_box("Doesn't work on Vimeo", msg.message_warning)
            return
            
        frm = util.fetch_youtube_format_from_url(
              url,
              self.youtube_format_tbl,
              self.global_message)
        if frm:
            self.choose_format_cmb.addItems(frm)
    
    def single_download_data_read(self):
        try:
            #data = str(self.process_single.readAll(), 'utf-8')
            #data = str(self.process_single.readLine(), 'cp949') # Windows 
            data = str(self.process_single.readLine(), ydlconf.get_encoding())
        except Exception as e:
            err_msg = "Error(single_download_data_read)\n"\
                      "... process_single.readLine\n... %s"%reutil._exception_msg(e)
            self.global_message.appendPlainText("=> %s\n"%err_msg)
            msg.message_box(err_msg, msg.message_error)
            return

        if reutil._find_ydl_warning(data):
            self.global_message.appendPlainText("=> %s\n"%data)
            
        if reutil._find_ydl_error(data):
            err_msg = "Error(single_download_data_read)\n... _find_ydl_error\n... %s"%data
            self.process_single_error = True
            self.global_message.appendPlainText("=> %s\n"%err_msg)
            msg.message_box(data, msg.message_error)
            return
            
        if reutil._file_exist(data):
            self.single_file_already_exist = True
            msg.message_box(ydlconst._ydl_const_exist_text, msg.message_normal)
            return

        fn = reutil._find_filename(data)
        if fn:
            fpath, fname = os.path.split(fn.strip())
            self.global_message.appendPlainText("=> Path: %s\n=> Name: %s\n"%(fpath, fname))
            return
                        
        match = reutil._find_percent.search(data)
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
            data = str(self.process_multiple.readLine(), ydlconf.get_encoding()) 
        except Exception as e:
            err_msg = "Error (multiple_download_data_read)\n"\
                      "... process_multiple.readLine\n... %s"%reutil._exception_msg(e)
            self.global_message.appendPlainText("=> %s\n"%err_msg)
            #msg.message_box(err_msg, msg.message_error)
            return
        
        if reutil._find_ydl_error(data):
            err_msg = "Error(multiple_download_data_read)\n"\
                      "... _find_ydl_error [%d-th]\n... %s"%(self.download_count, data)
            self.process_multiple_error = True
            self.youtube_path_tbl.item(self.download_count, 0).setBackground(ydlcolor._ydl_color_error)
            self.youtube_path_tbl.item(self.download_count, 2).setText("Error")
            self.global_message.appendPlainText("=> %s\n"%err_msg)
            #msg.message_box("URL: #%d\n%s"%(self.download_count,data), msg.message_error)
            return

        if reutil._file_exist(data):
            self.process_multiple_file_exist = True
            self.youtube_path_tbl.item(self.download_count, 0).setBackground(ydlcolor._ydl_color_file_exist)
            self.youtube_path_tbl.item(self.download_count, 2).setText(ydlcolor._ydl_const_exist_text)
            return

        fn = reutil._find_filename(data)
        if fn:
            fpath, fname = os.path.split(fn.strip())
            self.global_message.appendPlainText("=> Path: %s\n=> Name: %s"%(fpath, fname))
            return

        match = reutil._find_percent.search(data)

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
                self.youtube_path_tbl.item(self.download_count, 0).setBackground(ydlcolor._ydl_color_error)
                self.youtube_path_tbl.item(self.download_count, 2).setText("Error")
            elif self.process_multiple_file_exist is False:
                self.youtube_path_tbl.item(self.download_count, 0).setBackground(ydlcolor._ydl_color_finished)
                self.youtube_path_tbl.item(self.download_count, 2).setText("Finished")
            
            self.global_message.appendPlainText("=> Miltiple Download Done")
            self.print_download_elasped()
            return
            
        if self.process_multiple_error is False and self.process_multiple_file_exist is False:
            self.youtube_path_tbl.item(self.download_count, 0).setBackground(ydlcolor._ydl_color_finished)
            self.youtube_path_tbl.item(self.download_count, 2).setText("Finished")
            self.global_message.appendPlainText("=> %d-th download finished\n"%self.download_count)
                
        self.download_count += 1
        
        sublist = self.multiple_download_job_list[0]
        del self.multiple_download_job_list[0]
        
        try:
            self.process_multiple_error = False
            self.process_multiple_file_exis = False
            self.global_message.appendPlainText(util.cmd_to_msg(sublist[0], sublist[1]))
            self.process_multiple.start(sublist[0], sublist[1])
        except Exception as e:
            err_msg = "Error(multiple_download_finished)\n[%d-th]: %s"%\
                      (self.download_count, reutil._exception_msg(e))
            self.global_message.appendPlainText("=> %s\n"%err_msg)
            msg.message_box(err_msg, msg.message_yesno)
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
        elasped_time = util.hms_string(download_t2-self.download_t1)
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
        if self.multiple_download_method.currentText() == funs.get_sequential_download_text():
            self.global_message.appendPlainText("=> Cancel Multiple Download\n")
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
            
        if tab_text == funs.get_multiple_tab_text():    
            id = self.multiple_mood_AV_button_group.checkedId()
            fmt = self.global_download_format_btn.text()

            if fmt.find(ydlconst._ydl_format_none) < 0:
                arg_list.extend(["-f", re.search("\d+", fmt).group(0)])
            else:
                if id == 0: # audio only
                    audio_codec = self.multiple_download_audio_codec_cmb.currentText()
                    arg_list.extend([ ydlconst._ydl_option_extract_audio,
                                      ydlconst._ydl_option_audio_format,
                                      audio_codec])
                                    
                    if audio_codec != ydlconst._ydl_best_audio_codec:
                        arg_list.extend([ ydlconst._ydl_option_audio_quality, 
                                          self.multiple_download_audio_quality_cmb.currentText().split(' ')[0]])
                
                elif id == 1: # video
                    if self.multiple_download_video_codec_cmb.currentIndex() > 0:
                        arg_list.extend([ ydlconst._ydl_option_encode_video,
                                          self.multiple_download_video_codec_cmb.currentText()])
                                     
            save_folder = os.path.join(self.youtube_save_path.text(), ydlconst._ydl_option_output_filename)
            arg_list.extend([ ydlconst._ydl_option_output, save_folder])

            self.multiple_download_job_list = []
            arg_list.append(' ')
            
            for k in range(number_of_url):
                self.youtube_path_tbl.item(k,0).setBackground(QColor(255,255,255))
                self.youtube_path_tbl.item(k,2).setText("")
                arg_list[-1] = self.youtube_path_tbl.item(k,0).text().strip()
                job = [arg_list[0], arg_list[1:]]
                self.multiple_download_job_list.append(job)

            dm = self.multiple_download_method.currentText()
            
            if dm == funs.get_sequential_download_text():
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
                    self.multiple_download_timer.start(ydlconf.get_sequential_download_timer_interval(), self)
                
                self.multiple_download_progress.setTextVisible(True)
                self.multiple_download_progress.setFormat("Download: %p%")
                self.disable_multiple_download_buttons()
                self.download_t1 = time.time()
                self.download_count = 0
                self.process_multiple_error = False
                self.process_multiple_file_exist = False
                
                try:
                    self.global_message.appendPlainText("=> cmd\n%s %s\n"%(sublist[0], ' '.join(sublist[1])))
                    self.process_multiple.start(sublist[0], sublist[1])
                except Exception as e:
                    err_msg = "Error(start_multiple_download)\n"\
                              "Sequential [%d-th]: %s"%(self.download_count, reutil._exception_msg(e))
                    self.global_message.appendPlainText("=> %s\n"%err_msg)
                    msg.message_box(err_msg, msg.message_error)
                    self.delete_job_list()
                    self.enable_multiple_download_buttons()
                    
            elif dm == funs.get_concurrent_download_text():
                self.disable_multiple_parent_buttons()
                pc = ydlproc.ProcessController(self.multiple_download_job_list)
                #pt = ProcessTracker(pc, self.global_message) # modal
                pt = ProcessTracker(self, pc, self.global_message)
                pc.status_changed.connect(self.set_download_status)
                pc.print_message.connect(self.print_concurrent_message)
                pt.status_changed.connect(self.set_download_button_status)
                #pt.exec_() #modal
                pt.show()
                
    def print_concurrent_message(self, con_msg):
        self.global_message.appendPlainText(con_msg)
        
    def set_download_button_status(self, status):
        if status == ydlconst._ydl_download_start:
            for k in range(self.youtube_path_tbl.rowCount()):
                self.youtube_path_tbl.item(k,0).setBackground(ydlcolor._ydl_color_white)
                self.youtube_path_tbl.item(k,2).setText("")
        elif status == ydlconst._ydl_download_finish:
            self.enable_multiple_parent_buttons()
            
    def set_download_status(self, proc):
        key_num = int(proc.key.split(' ')[1])-1
        if proc.file_exist:
            self.youtube_path_tbl.item(key_num, 0).setBackground(ydlcolor._ydl_color_file_exist)
            self.youtube_path_tbl.item(key_num, 2).setText("Already exist")
        elif proc.error:
            self.youtube_path_tbl.item(key_num, 0).setBackground(ydlcolor._ydl_color_error)
            self.youtube_path_tbl.item(key_num, 2).setText("Error")
            self.global_message.appendPlainText(proc.status)
        else:
            self.youtube_path_tbl.item(key_num, 0).setBackground(ydlcolor._ydl_color_finished)
            self.youtube_path_tbl.item(key_num, 2).setText("Finished")
            
    def start_single_download(self):
        url = self.youtube_url.text()
        #match = reutil._valid_youtube_url.search(url)
        #if not match:
        #    msg.message_box("Invalid URL", msg.message_error)
        #    return
        
        tab_text = self.youtube_tabs.tabText(self.youtube_tabs.currentIndex())
        
        arg_list = ['youtube-dl']
        self.single_download_step = 0
            
        if tab_text == funs.get_single_tab_text():
        
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
                    arg_list.extend([ ydlconst._ydl_option_extract_audio,
                                      ydlconst._ydl_option_audio_format,
                                      audio_codec])
                                    
                    if audio_codec != ydlconst._ydl_best_audio_codec:
                        arg_list.extend([ ydlconst._ydl_option_audio_quality, 
                                          self.single_download_audio_quality_cmb.currentText().split()[0]])
                
                elif id == 1: # video
                    cur_vcodec = self.single_download_video_codec_cmb.currentText()
                    if cur_vcodec != funs.get_best_codec_name():
                        arg_list.extend([ ydlconst._ydl_option_encode_video,
                                          cur_vcodec
                                        ])
            # Postprocess downloaded file w/ FFMpeg
            # Cut the video/audio 
            if self.single_download_ffmpeg_config.use_ffmpeg:
                if id==1 and (cur_vcodec == funs.get_best_codec_name() or\
                              cur_vcodec == funs.get_mkv_codec_name()) and\
                              self.single_download_ffmpeg_config.bypass_mkv:
                    # Bypassing mkv warning:
                    # Enforce the codec as mp4 because it's impossible to predict
                    # if the video will be put into MKV becuase of high quality
                    arg_list.extend(['-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]'])
                    
                arg_list.extend([ ydlconst._ydl_option_choose_ffmpeg, 
                                  ydlconst._ydl_option_ffmpeg_argument,
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
            
            save_folder = os.path.join(self.youtube_save_path.text(), ydlconst._ydl_option_output_filename)
            arg_list.extend([ ydlconst._ydl_option_output, save_folder, url.strip()])
            
            self.single_download_job_list=[[arg_list[0], arg_list[1:]]]
            
            sublist = self.single_download_job_list[0]
            del self.single_download_job_list[0]
            
            if self.single_download_timer.isActive():
                self.single_download_timer.stop()
            else:
                #self.single_download_timer.start(100, self)
                self.single_download_timer.start(ydlconf.get_single_download_timer_interval(), self)
            
            self.single_download_progress.setTextVisible(True)
            self.single_download_progress.setFormat("Download: %p%")
            self.disable_single_download_buttons()
            self.download_t1 = time.time()
            self.process_single_error = False
            self.single_file_already_exist = False
            try:
                self.global_message.appendPlainText("=> cmd\n%s %s\n"%(sublist[0], ' '.join(sublist[1])))
                self.process_single.start(sublist[0], sublist[1])
            except Exception as e:
                err_msg = "Error(start_single_download)\n%s"%reutil._exception_msg(e)
                self.global_message.appendPlainText("=> %s\n"%err_msg)
                msg.message_box(err_msg, msg.message_error)
                self.enable_single_download_buttons()
    
    def cancel_single_download(self):
        if not self.process_single: return
        tab_text = self.youtube_tabs.tabText(self.youtube_tabs.currentIndex())
        self.global_message.appendPlainText("=> Cancel single download")
        if tab_text == funs.get_single_tab_text():
            self.process_single.kill()
            self.single_download_timer.stop()
    
def main():
    global _clipboard
    
    app = QApplication(sys.argv)
    _clipboard = app.clipboard()

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

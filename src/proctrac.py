import time
from collections import OrderedDict
from functools import partial

from PyQt5.QtCore import Qt, pyqtSignal, QObject, QProcess, QSize, QBasicTimer
from PyQt5.QtGui import QColor, QIcon, QPixmap, QIntValidator, QFont, QFontMetrics
from PyQt5.QtWidgets import ( #QApplication, 
                              QWidget,
                              #QStyleFactory, 
                              QDialog,
                              #QLabel, 
                              QPushButton, 
                              #QLineEdit,
                              #QComboBox, 
                              #QCheckBox, 
                              #QRadioButton, 
                              #QTableWidget, 
                              #QTableWidgetItem, 
                              #QTabWidget,
                              QProgressBar, 
                              #QPlainTextEdit, 
                              QGridLayout, 
                              QVBoxLayout, 
                              QHBoxLayout, 
                              QFormLayout, 
                              #QButtonGroup,
                              #QFileDialog, 
                              QScrollArea,
                              QMessageBox,
                              #QHeaderView,
                              #QButtonGroup,
                              #QGroupBox,
                              #QTreeWidget,
                              #QTreeWidgetItem
                              )


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
        #self.scroll.setMaximumHeight(200)
        self.scroll.setMaximumHeight(ydlconf.get_tacker_max_height())
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
            #self.timer.start(100, self)
            self.timer.start(ydlconf.get_concurrent_download_timer_interval(), self)
        
        try:
            self.proc_ctrl.start()
        except Exception as e:
            msg.message_box("Error: %s"%e, msg.message_error)
            self.msg.appendPlainText("=> Error: %s"%e)
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

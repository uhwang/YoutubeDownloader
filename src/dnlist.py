'''
    dnlist.py
    
    Youtube Downloader: Create Download List from URL w/ list type

    Author: Uisang Hwang
    
    https://www.youtube.com/watch?v= 
    
'''
#from PyQt4.QtCore import Qt, QObject, QProcess, pyqtSignal
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QProcess

import util
import reutil
import ydlproc
import ydlconst
import ydlconf

class QCreateVideoListFromURL(QObject):

    status_changed = pyqtSignal(str)
    
    def __init__(self, url, pmsg):
        super(QCreateVideoListFromURL, self).__init__()
        self._video_list = list()
        self._proc = None
        self._cur_sequence = 0
        self._video_count = 0
        self._url = url
        self._msg = pmsg
        
    def create_video_list_from_youtube_url(self):
        self.proc = QProcess()
        self.proc.setReadChannel(QProcess.StandardOutput)
        self.proc.setProcessChannelMode(QProcess.MergedChannels)
        self.proc.finished.connect(self.read_finished)
        self.proc.readyRead.connect(self.read_data)
        self.proc.start("youtube-dl", ["-F", self._url])
    
    def cancel(self):
        if self.proc: 
            self.proc.kill()
        
    def read_finished(self):
        if self._cur_sequence == self._video_count:
            self._msg.appendPlainText("... URL List Finished!")
    
    def finished(self):
        return self._cur_sequence == self._video_count
        
    def read_data(self):
        
        try:
            #data = str(self.proc.readLine(), 'cp949') # Windows 
            data = str(self.proc.readAll(), ydlconf.get_encoding()) # Windows 
        except Exception as e:
            self._msg.appendPlainText(_exception_msg(e))
            return
            
        if reutil._find_error.search(data):
            self._msg.appendPlainText(data)
            self.status_changed.emit(data)
            return
            
        m = reutil._find_video_sequence.search(data)
        if m:
            self._cur_sequence += 1
            self._video_count = int(m[2])
           
        p = data.find("[info]")           
        if p > -1:
            s = data[p:data.find(':')]
            url = s[s.rfind(' ')+1:]
            self._video_list.append(ydlconst._ydl_url_prefix+url)
            self.status_changed.emit("... %d of %d: %s"%\
            (self._cur_sequence, self._video_count, url))
                

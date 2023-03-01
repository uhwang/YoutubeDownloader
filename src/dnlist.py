'''
    dnlist.py
    
    Youtube Downloader: Create Download List from URL w/ list type

    Author: Uisang Hwang
    
    02/23/23    Fix code for yt-dlp (youtube-dl: no more update)
    02/27/23    Catch invalid video url

    https://www.youtube.com/watch?v= 
    
'''
#from PyQt4.QtCore import Qt, QObject, QProcess, pyqtSignal
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QProcess
from collections import OrderedDict

import util
import reutil
import ydlproc
import ydlconst
import ydlconf
import msg

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
        self._invalid_video_url = []
        self._invalid_video_sequence = []
        
    def create_video_list_from_youtube_url(self):
        self.proc = QProcess()
        self.proc.setReadChannel(QProcess.StandardOutput)
        #self.proc.setProcessChannelMode(QProcess.MergedChannels)
        self.proc.setProcessChannelMode(QProcess.SeparateChannels)
        self.proc.finished.connect(self.read_finished)
        self.proc.readyRead.connect(self.read_data)
        self.proc.start(ydlconf.get_executable_name(), ["-F", self._url])
    
    def cancel(self):
        if self.proc: 
            self.proc.kill()
        
    def read_finished(self):
        if self._cur_sequence == self._video_count:
            final_msg = "... URL List Finished!\n"
            if self._video_count == 0:
                self._msg.appendPlainText("==> WARNING : check URL")
                
            if self._invalid_video_url:
                self._invalid_video_sequence = [
                      i+1 for i, v in enumerate(self._video_list)
                      if v in self._invalid_video_url]
            
                final_msg += "... Invalid video(%d)\n"\
                             "==> %s"\
                             %(len(self._invalid_video_url),
                             ' '.join(map(str,self._invalid_video_sequence)))
            # this signal is for enable start button.
            self.status_changed.emit(ydlconst._ydl_const_finished)
            self._msg.appendPlainText(final_msg)
    
    def finished(self):
        return self._cur_sequence == self._video_count
        
    def read_data(self):
        
        try:
            url_data = str(self.proc.readAll(), ydlconf.get_encoding())
            url_error = str(self.proc.readAllStandardError(), ydlconf.get_encoding())
        except Exception as e:
            err_msg = "Exception (QCreateVideoListFromURL)\n"\
                      "... proc.readAll()\n... %s"%reutil._exception_msg(e)
            self._msg.appendPlainText(err_msg)
            return

        #m = reutil._find_video_sequence.search(data)
        m = reutil._find_playlist_sequence.search(url_data)
        if m:
            self._cur_sequence = int(m[1])
            self._video_count = int(m[2])
            
        if reutil._find_error.search(url_error):
            err_msg = "Error (QCreateVideoListFromURL)\n"\
                      "... _find_error\n... %s"%url_error
            self._msg.appendPlainText(err_msg)
            p1 = err_msg.rfind(": Video unavailable")
            if p1 > -1:
                p2=err_msg.find(']')+1
                invalid_url=err_msg[p2:p1].strip()
                self._invalid_video_url.append(invalid_url)
            return
            
        u1 = url_data.split('\n')
        for u2 in u1:
            p = u2.find("?v=")
            if p > -1: 
                url = u2[p+3:].strip()
                self._video_list.append(url)
                self._msg.appendPlainText("... %d of %d: %s"%(self._cur_sequence, self._video_count, url))
            #self.status_changed.emit("... %d of %d: %s"%\
            #(self._cur_sequence, self._video_count, url))
            
        '''   
        p = url_data.find("[info]")           
        if p > -1:
            s = url_data[p:url_data.find(':')]
            url = s[s.rfind(' ')+1:]
            self._video_list.append(url)
            self.status_changed.emit("... %d of %d: %s"%\
            (self._cur_sequence, self._video_count, url))
        '''
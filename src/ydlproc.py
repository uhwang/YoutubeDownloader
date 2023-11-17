'''
    ydlproc.py
    
    Author: Uisang Hwang
    
    https://www.youtube.com/watch?v= 
    
'''
from collections import OrderedDict
from functools import partial
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QObject, QProcess
import reutil
import ydlconf

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
    print_message =  pyqtSignal(str)

    def __init__(self, job_list, formula = "Proc %d", start_key=0):
        super(ProcessController, self).__init__()
        self.job_list = job_list
        self.nproc = 0
        self.proc_pool = None
        self.key_formula = formula
        self.start_key = start_key

    def start(self):
        self.proc_pool = OrderedDict()
        self.nproc = 0
        
        for k, _ in enumerate(self.job_list):
            key = self.key_formula%(k+1+self.start_key)
            proc = QProcessProgress(key)
            proc.setReadChannel(QProcess.StandardOutput)
            proc.setProcessChannelMode(QProcess.MergedChannels)
            proc.finished.connect(partial(self.check_finshed,key))
            proc.readyRead.connect(partial(self.read_data,key))
            self.proc_pool[key] = proc
            self.nproc += 1

        for j, p in zip(self.job_list, self.proc_pool.values()):
            self.print_message.emit("=> cmd(%s)\n%s %s\n"%(p.key, j[0],' '.join(j[1])))
            p.start(j[0], j[1])
            
    def check_finshed(self, key):
        if not self.proc_pool: 
            return
        
        self.nproc -= 1
        #if reutil._find_ydl_error(self.data):
        #    proc.error = True
        #    proc.status = "=> Error(ProcessController)\n"\
        #                  "... read_data (_find_ydl_error)\n"\
        #                  "... [%s] : %s\n"%\
        #                  (key,self.data)
        #    self.status_changed.emit(proc)
        #    return
            
        if not self.proc_pool[key].file_exist and\
           not self.proc_pool[key].error:
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
        proc = self.proc_pool[key]
        self.data = None
        try:
            self.data = str(proc.readLine(), ydlconf.get_encoding())
            #data = str(proc.readLine(), 'cp949') # For Windows
            #data = str(proc.readLine(), 'utf-8') 
        except Exception as e:
            proc.error = True
            proc.status = "=> Error(ProcessController)\n"\
                          "... read_data (proc.readLine)\n"\
                          "... [%s] : %s\n... %s"%\
                          (key, reutil._exception_msg(e), 
                          self.data if self.data else "No data received")
            proc.step = 100
            self.status_changed.emit(proc)
            return
            
        if reutil._find_ydl_error(self.data):
            proc.error = True
            proc.status = "=> Error(ProcessController)\n"\
                          "... read_data (_find_ydl_error)\n"\
                          "... [%s] : %s\n"%\
                          (key,self.data)
            proc.step = 100
            self.status_changed.emit(proc)
            return
            
        if reutil._file_exist(self.data):
            proc.file_exist = True
            proc.status = "already exist"
            proc.step = 100
            self.status_changed.emit(proc)
            return
                       
        match = reutil._find_percent.search(self.data)
        if match:
            proc.step = int(float(match.group(0)[:-1]))


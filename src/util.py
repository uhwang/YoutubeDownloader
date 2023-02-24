'''
    util.py
    
    Youtube Downloader: Create Download List from URL w/ list type

    02/23/22    Fix code for yt-dlp (youtube-dl: no more update)

    Author: Uisang Hwang
    
'''
import re
import msg
import subprocess as sp
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtCore import QProcess

import ydlconst
import ydlconf
import reutil
from functools import partial

_format_data = None
#_find_valid_string = re.compile()
# edit : QLineEdit
def clear_url_input(edit):
    edit.clear()

def copy_url_input(edit, clipboard):
    edit.setText(clipboard.text())
    
def time_to_sec(t1):
    t2 = reutil._find_time.search(t1)
    sec = 60*(int(t2.group(1))*60+int(t2.group(2)))+int(t2.group(3))+ float(t2.group(4))*.01
    return sec
    
def get_youtube_formats(url, pmsg=None):
    cmd=[ ydlconf.get_executable_name(), #'youtube-dl',
          ydlconst._ydl_option_socket_timeout, 
          "%s"%ydlconf.get_fetch_timeout_duration(),
          '-F', url]
    
    try:
        # https://docs.python.org/3/library/subprocess.html
        # If you wish to capture and combine both streams into one, 
        # use stdout=PIPE and stderr=STDOUT instead of capture_output.
        # youtube-dl emits error and warning to stderr
        proc = sp.Popen(cmd, stdout=sp.PIPE, stderr = sp.STDOUT)
    except Exception as e:
        err_msg = "=> Error(get_youtube_formats)\n"\
                  "... sp.Popen : %s\n"%reutil._exception_msg(e)
        if pmsg: pmsg.appendPlainText(err_msg)
        msg.message_box(err_msg, msg.message_error)
        return None
    	
    output = proc.communicate()[0]
    # http:#stackoverflow.com/questions/606191/convert-bytes-to-a-python-string
    #output = output.decode('utf-8')
    output = output.decode(ydlconf.get_encoding())

    # output is a long stream characters
    if reutil._find_error.search(output):
        err_msg = "=> Error(get_youtube_formats)\n"\
                  "... _find_error : %s"%output
        if pmsg: pmsg.appendPlainText(err_msg)
        msg.message_box("Error: can't fetch formats\nCheck the message!", msg.message_error)
        return None

    # count commnet lines
    skip_comment = 0
    # output is a list of strings
    output = output.split('\n')
    for o in output:
        o.strip()
        #if reutil._find_digit.search(o[0:o.find(' ')]):
        if reutil._find_digit_only.search(o[0:o.find(' ')]):
            break
        skip_comment += 1
     
    #formats = output[skip_comment:]

    #formats = [o.replace('|','') for o in output[skip_comment:]]
    formats = [re.sub('[|~]','', o) for o in output[skip_comment:]]
    
    if not reutil._find_valid_string.findall(formats[-1]):
        del formats[-1]
    
    for i, f in enumerate(formats):
        if f.find("video only") > -1 or f.find("audio only") > -1:
            continue
        else:
            if reutil._find_resolution.search(f): 
                ff = formats.pop(i)
                formats.append(ff)
    
    del proc
    
    return formats

def get_youtube_format_from_formats(format):

    e = reutil._find_format.findall(format)
    #filesize = reutil._find_file_size(format)
    #bitrate = reutil._find_bitrate.search(format)
    #format_elem = re.findall(r'\S+', format)
    format_elem = reutil._find_valid_string.findall(format)

    if len(e) < 1: return None
    
    # code  ext  res                 size                      bit   type
    # ID    EXT  RESOLUTION  FPS  CH FILESIZE TBR PROTO VCODEC VBR ACODEC ABR ASR MORE INFO
    if format.find('audio') > -1:
        filesize = format_elem[5]
        #fm = [ e[0], e[1], e[2], bitrate[0], filesize[0], 'audio only']
        fm = [ 
                format_elem[0], 
                format_elem[1], 
                'N/A', 
                format_elem[11], 
                filesize, 
                'audio only']
    else:
        #fm = [ e[0], e[1], e[2], bitrate[0], 
        #       filesize[0] if filesize else "best" if format.find("best")>-1 else "N/A",
        #       'video only' if format.find('video only')>-1 else "video"]
        
        # check 4th elem is channel 1 or 2
        # 17  3gp   176x144     12  1 192.62KiB
        if format_elem[4].isdigit():
            filesize = format_elem[5] 
            vbr = format_elem[9] 
        else:
            filesize = format_elem[4]
            vbr = format_elem[8] 
        fm = [
                format_elem[0], 
                format_elem[1], 
                format_elem[2], 
                vbr,
                filesize,
                'video only' if format.find('video only')>-1 else "video"
                ]
    return fm
    
def fetch_youtube_format_from_url(url, tbl, pmsg=None):

    #if not reutil._valid_youtube_url.search(url):
    #    msg.message_box("Invalid URL", msg.message_error)
    #    return None

    if url == '':
        return None
    
    formats = get_youtube_formats(url, pmsg)
    if formats == None: 
        return None
    
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

#https://arcpy.wordpress.com/2012/04/20/146/    
def hms_string(sec_elapsed):
    h = int(sec_elapsed / (60 * 60))
    m = int((sec_elapsed % (60 * 60)) / 60)
    s = sec_elapsed % 60.
    return "{}:{:>02}:{:>05.2f}".format(h, m, s)
 
def cmd_to_msg(self, cmd, arg=""):
    if isinstance(cmd, (list,)): msg1 = ' '.join(cmd)
    elif isinstance(cmd, (str,)): msg1 = cmd
    else: msg1 = "Invalid cmd type: %s"%type(cmd)
    
    if isinstance(arg, (list,)): msg2 = ' '.join(arg)
    elif isinstance(arg, (str,)): msg2 = arg
    else: msg2 = "Invalid arg type: %s"%type(arg)
    
    return "=> %s %s"%(msg1, msg2) 
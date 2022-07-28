'''
    util.py
    
    Youtube Downloader: Create Download List from URL w/ list type

    Author: Uisang Hwang
    
'''
import re
import msg
import subprocess as sp
from PyQt5.QtWidgets import QTableWidgetItem

import ydlconst
import ydlconf
import reutil

def time_to_sec(t1):
    t2 = reutil._find_time.search(t1)
    sec = 60*(int(t2.group(1))*60+int(t2.group(2)))+int(t2.group(3))+ float(t2.group(4))*.01
    return sec
    
def get_youtube_formats(url, pmsg=None):
    cmd=[ 'youtube-dl',
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
        if pmsg: pmsg.appendPlainText("=> Fetch formats\n=> Error: %s\n=> %s\n"%(str(e), cmd))
        msg.message_box(str(e), msg.message_error)
        return None
    	
    output = proc.communicate()[0]
    # http:#stackoverflow.com/questions/606191/convert-bytes-to-a-python-string
    #output = output.decode('utf-8')
    output = output.decode(ydlconf.get_encoding())

    # output is a long stream characters
    if reutil._find_error.search(output):
        if pmsg: pmsg.appendPlainText(output)
        msg.message_box("Can't fetch formats\nYou might have network problem\nCheck message", msg.message_error)
        return None

    # output is a list of strings
    output = output.split('\n')
    
    # count commnet lines
    skip_comment = 0
    for o in output:
        o.strip()
        if reutil._find_digit.search(o[0:o.find(' ')]):
            break
        skip_comment += 1
     
    formats = output[skip_comment:]
    del proc
    
    return formats

def get_youtube_format_from_formats(format):

    e = reutil._find_format.findall(format)
    filesize = reutil._find_file_size(format)
    bitrate = reutil._find_bitrate.search(format)

    if len(e) < 1: return None
    
    if format.find('audio') > -1:
        fm = [ e[0], e[1], e[2], bitrate[0], filesize[0], 'audio only']
    else:
        fm = [ e[0], e[1], e[2], bitrate[0], 
               filesize[0] if filesize else "best" if format.find("best")>-1 else "N/A",
               'video only' if format.find('video only')>-1 else "video"]
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
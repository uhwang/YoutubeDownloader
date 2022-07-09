'''
    xrefcom.py
    
    2/3/21  Ver 0.1

'''

from PyQt5.QtWidgets import QMessageBox
#from PyQt4.QtGui import QMessageBox

message_type = ('normal', 'yesno', 'warning', 'error')

message_normal = 0
message_yesno  = 1
message_warning= 2
message_error  = 3

message_type_icon = {
    message_type[message_normal ]: QMessageBox.Information, 
    message_type[message_yesno  ]: QMessageBox.Question, 
    message_type[message_warning]: QMessageBox.Warning, 
    message_type[message_error  ]: QMessageBox.Critical
}

message_type_button = {
    message_type[message_normal ]: QMessageBox.Ok, 
    message_type[message_yesno  ]: QMessageBox.Yes|QMessageBox.No, 
    message_type[message_warning]: QMessageBox.Ok, 
    message_type[message_error  ]: QMessageBox.Ok
}

def message_box(e_str, type):
    
    msg = QMessageBox()
    msg.setIcon(message_type_icon[message_type[type]])
    msg.setStandardButtons(message_type_button[message_type[type]])
    msg.setEscapeButton(QMessageBox.No)
    msg.setText(e_str)
    return msg.exec_()
    
    
    

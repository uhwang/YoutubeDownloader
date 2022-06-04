'''
    xrefcom.py
    
    2/3/21  Ver 0.1

'''

from PyQt4.QtGui import QMessageBox

message_type = ('normal', 'warning', 'error')

message_normal = 0
message_warning= 1
message_error  = 2

message_type_icon = {
    message_type[message_normal ]: QMessageBox.Information, 
    message_type[message_warning]: QMessageBox.Question, 
    message_type[message_error  ]: QMessageBox.Critical
}

def message_box(e_str, type):
    
    msg = QMessageBox()
    msg.setIcon(message_type_icon[message_type[type]])
    msg.setStandardButtons(QMessageBox.Ok)
    msg.setText(e_str)
    
    return_value = msg.exec_()
    return True if return_value == QMessageBox.Ok else False
    
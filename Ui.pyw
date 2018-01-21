# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\pyprojects\qa\GUI.ui'
#
# Created by: PyQt5 UI code generator 5.9
#
# WARNING! All changes made in this file will be lost!

import traceback
import time

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QImage,QPixmap
from PyQt5.QtWidgets import QMessageBox

from client import *


class T_login(QtCore.QThread):
    SIG_LOGIN=QtCore.pyqtSignal(bool,int)
    def __init__(self,uname,passwd):
        super(T_login,self).__init__()
        self.uname,self.passwd=uname,passwd
        
    def run(self):
        response=post_login(self.uname,self.passwd)
        enable=bool(response.get('enable',False))
        number=int(response.get('number',0))
        self.SIG_LOGIN.emit(enable,number)
        
class T_read(QtCore.QThread):
    SIG_SCREEN=QtCore.pyqtSignal(list)
    SIG_TYPE=QtCore.pyqtSignal(str)
    
    SIG_LOGIN=QtCore.pyqtSignal(bool,int)

    SIG_RESULT=QtCore.pyqtSignal(list)
    SIG_ANSWER=QtCore.pyqtSignal(str)
    
    SIG_END=QtCore.pyqtSignal()
    def __init__(self,uname,passwd):
        super(T_read,self).__init__()
        self.uname,self.passwd=uname,passwd
        self.n=0
        
    def run(self):
        response,frame,bound,state,scale=None,None,None,None,None
        got_answer=False
        while self.n<10:
            binary,gray,frame,scale=pull_screenshot()
            self.SIG_SCREEN.emit([frame])
            
            try:
                roi,bound,state=get_roi(binary,gray,frame)
            except (NoCircle,NoLine):
                traceback.print_exc()
                self.n+=1
                time.sleep(0.5)
                continue
            except:
                traceback.print_exc()
                self.SIG_TYPE.emit('Got unexpected ERROR, retrying...')
                self.n+=1
                time.sleep(0.5)
                continue
            if state=='q':
                self.n+=1
                time.sleep(0.5)
                continue
            self.SIG_TYPE.emit('Text type :{}.'.format('question only' if state=='q' else 'question and answer'))
            content=rgb_to_content(roi)
            response=post_read(self.uname,self.passwd,content)
            enable=bool(response.get('enable',False))
            number=int(response.get('number',0))
            if enable and number>0:
                print(response.get('error_msg','No error'))
                question,answers,nbs,probs,reference=get_result(response,bound,state)
                answer_text=show_result(question,answers,nbs,probs,reference)
                self.SIG_ANSWER.emit(answer_text)
                self.SIG_RESULT.emit([response,frame,bound,state,scale])
                self.SIG_END.emit()
                break
            else:
                self.SIG_LOGIN.emit(enable,number)
                
        
class UIQA(object):
    def __init__(self,Dialog):
        self.dialog=Dialog
        
        self.enable=False
        self.passwd_path='./passwd.cfg'
        if os.path.exists(self.passwd_path):
            with open(self.passwd_path,'r') as f:
                text=f.read()
                self.uname,self.passwd=text.split('\n')
                self.loaded=True
        else:
             self.uname,self.passwd=' ',' '
             self.loaded=False
             
        self.stop=False
        
    def setupUi(self):
        self.dialog.setObjectName("Dialog")
        self.dialog.resize(720, 640)
        self.dialog.setSizeGripEnabled(True)
        self.gridLayout_4 = QtWidgets.QGridLayout(self.dialog)
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.gridLayout_3 = QtWidgets.QGridLayout()
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.gb_login = QtWidgets.QGroupBox(self.dialog)
        self.gb_login.setObjectName("gb_login")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.gb_login)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.le_uname = QtWidgets.QLineEdit(self.gb_login)
        self.le_uname.setObjectName("le_uname")
        self.le_uname.setText('Enter ID' if not self.loaded else self.uname)
        self.gridLayout_2.addWidget(self.le_uname, 0, 0, 1, 1)
        self.pb_login = QtWidgets.QPushButton(self.gb_login)
        self.pb_login.setObjectName("pb_login")
        self.rb_remember=QtWidgets.QRadioButton(self.gb_login)
        self.rb_remember.setText('Remember me')
        self.rb_remember.setChecked(self.loaded)
        self.gridLayout_2.addWidget(self.rb_remember, 1, 1, 2, 1)
        self.gridLayout_2.addWidget(self.pb_login, 0, 1, 2, 1)
        self.le_passwd = QtWidgets.QLineEdit(self.gb_login)
        self.le_passwd.setObjectName("le_passwd")
        self.le_passwd.setText('Enter password' if not self.loaded else self.passwd)
        self.gridLayout_2.addWidget(self.le_passwd, 1, 0, 1, 1)
        
        self.gridLayout_3.addWidget(self.gb_login, 0, 0, 1, 1)
        self.pb_answer = QtWidgets.QPushButton(self.dialog)
        self.pb_answer.setObjectName("pb_answer")
        self.gridLayout_3.addWidget(self.pb_answer, 1, 0, 1, 1)
        self.groupBox = QtWidgets.QGroupBox(self.dialog)
        self.groupBox.setObjectName("groupBox")
        self.gridLayout = QtWidgets.QGridLayout(self.groupBox)
        self.gridLayout.setObjectName("gridLayout")
        self.rb_auto = QtWidgets.QRadioButton(self.groupBox)
        self.rb_auto.setObjectName("rb_auto")
        self.gridLayout.addWidget(self.rb_auto, 0, 0, 1, 1)
        self.pb_clean = QtWidgets.QPushButton(self.groupBox)
        self.pb_clean.setObjectName("pb_clean")
        self.gridLayout.addWidget(self.pb_clean, 0, 2, 1, 1)
        self.pb_stop = QtWidgets.QPushButton(self.groupBox)
        self.pb_stop.setText('Stop')
        self.gridLayout.addWidget(self.pb_stop, 0, 1, 1, 1)
        self.gridLayout_3.addWidget(self.groupBox, 2, 0, 1, 1)
        self.tb_answer = QtWidgets.QTextBrowser(self.dialog)
        self.tb_answer.setObjectName("tb_answer")
        self.gridLayout_3.addWidget(self.tb_answer, 3, 0, 1, 1)
        self.gridLayout_4.addLayout(self.gridLayout_3, 0, 0, 1, 1)
        self.lb_screen = QtWidgets.QLabel(self.dialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lb_screen.sizePolicy().hasHeightForWidth())
        self.lb_screen.setSizePolicy(sizePolicy)
        self.lb_screen.setText("Scrennshot")
        self.lb_screen.setObjectName("lb_screen")
        self.gridLayout_4.addWidget(self.lb_screen, 0, 1, 1, 1)

        
        self.retranslateUi()
        QtCore.QMetaObject.connectSlotsByName(self.dialog)

    def retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.gb_login.setTitle(_translate("Dialog", "Login"))
        self.pb_login.setText(_translate("Dialog", "login"))
        self.pb_answer.setText(_translate("Dialog", "Get answer"))
        self.groupBox.setTitle(_translate("Dialog", "选项"))
        self.rb_auto.setText(_translate("Dialog", "Auto"))
        self.pb_clean.setText(_translate("Dialog", "Clean config"))
        
    def set_connect(self):
        self.pb_login.clicked.connect(self.start_login)
        self.pb_answer.clicked.connect(self.start_read_screen)
        self.pb_stop.clicked.connect(self.stop_auto)
        
    def start_login(self):
        
        self.uname,self.passwd=self.le_uname.text(),self.le_passwd.text()
        self.login_thread=T_login(self.uname,self.passwd)
        self.login_thread.SIG_LOGIN.connect(self.finish_login)
        self.login_thread.start()
        
    def finish_login(self,enable,number):
        self.enable=enable
        if not self.enable:
            QMessageBox.warning(self.dialog,'登录失败','尝试以\n用户名：{}\n密码：{}\n登录失败，请检查后重试！')
        else:
            if self.rb_remember.isChecked():
                with open(self.passwd_path,'w') as f:
                    f.write(self.uname+'\n'+self.passwd)
            if number>0:
                QMessageBox.information(self.dialog,'登录成功','登录成功，欢迎使用！\n剩余请求次数{}次'.format(number))
            else:
                QMessageBox.warning(self.dialog,'剩余次数不足','剩余请求次数不足！'.format(number))
                self.enable=False
                
            
    def stop_auto(self):
        self.stop=True
        
    def start_read_screen(self):
        self.read_thread=T_read(self.uname,self.passwd)
        self.read_thread.SIG_SCREEN.connect(self._set_img)
# =============================================================================
#         self.read_thread.SIG_TYPE.connect(self.tb_answer.setText)
# =============================================================================
# =============================================================================
#         self.read_thread.SIG_RESULT.connect(self.get_answer)
# =============================================================================
        self.read_thread.SIG_ANSWER.connect(self.tb_answer.setText)
        self.read_thread.SIG_END.connect(self.re_read)
        self.read_thread.start()
    
    def re_read(self):
        if self.rb_auto.isChecked():
            self.start_read_screen()
    def _cv2qimg(self,cvImg):
        '''
        将opencv的图片转换为QImage
        '''
        height, width, channel = cvImg.shape
        bytesPerLine = 3 * width
        return QImage(cv2.cvtColor(cvImg,cv2.COLOR_BGR2RGB).data, width, height, bytesPerLine, QImage.Format_RGB888)
        
    def _set_img(self,cvImg_list):
        '''
        显示pixmap
        '''
        self.lb_screen.setPixmap(QPixmap.fromImage(self._cv2qimg(cvImg_list[0])))

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Dialog = QtWidgets.QDialog()
    ui = UIQA(Dialog)
    ui.setupUi()
    ui.set_connect()
    Dialog.show()
    sys.exit(app.exec_())


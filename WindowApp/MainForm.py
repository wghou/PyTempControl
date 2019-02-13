# -*- coding: utf-8 -*-

import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow
from WindowApp.MainWindow import Ui_MainWindow
from WindowApp.SettingForm import SettingForm
from PyQt5.QtCore import *


class MainForm(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainForm,self).__init__()
        self.setupUi(self)
        self.settingForm = SettingForm()
        self.settingForm.setWindowModality(Qt.ApplicationModal)
        self.pushButton_auto.clicked.connect(self._click)

    def _click(self):
        self.wk = RelayComThread()
        self.wk.finishSignal.connect(self._endwk)
        self.wk.my_start()

    def _endwk(self):
        print('end wk')


class RelayComThread(QtCore.QThread):
    """
    communicate with relay device in a new thread
    after finish, emit a signal with parameter RelayProtocol.ErrRelay
    """
    # finish signal
    finishSignal = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        print('init th')
        super(RelayComThread, self).__init__(parent)

    def my_start(self):
        print('my start')
        self.start()

    def run(self):
        import time
        print('run')
        time.sleep(5)
        print('run end, and emit')
        self.finishSignal.emit(3)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MainForm()
    w.show()
    w.settingForm.show()
    sys.exit(app.exec_())


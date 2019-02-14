# -*- coding: utf-8 -*-

import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow
from WindowApp.MainWindow import Ui_MainWindow
from WindowApp.SettingForm import SettingForm
from PyQt5.QtCore import *
from Device.Devices import *


class MainForm(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainForm,self).__init__()
        self.devAll = Devices()
        self.setupUi(self)
        self.settingForm = SettingForm()
        self.settingForm.setWindowModality(Qt.ApplicationModal)
        self.pushButton_auto.clicked.connect(self._clicked_auto)
        self.pushButton_param.clicked.connect(self._clicked_param)

        self._set_device()

    def _clicked_auto(self):
        pass

    def _clicked_param(self):
        self.settingForm.show()

    def _set_device(self):
        self.devAll.start_timer()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MainForm()
    w.show()
    w.settingForm.show()
    sys.exit(app.exec_())


# -*- coding: utf-8 -*-

import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QDialog
from WindowApp.ParamSettingWindow import Ui_Dialog


class SettingForm(QDialog, Ui_Dialog):
    def __init__(self):
        super(SettingForm,self).__init__()
        self.setupUi(self)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = SettingForm()
    w.show()
    sys.exit(app.exec_())


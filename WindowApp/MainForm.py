# -*- coding: utf-8 -*-

import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow
from WindowApp.MainWindow import Ui_MainWindow
from WindowApp.SettingForm import SettingForm


class MainForm(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainForm,self).__init__()
        self.setupUi(self)
        self.settingForm = SettingForm()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MainForm()
    w.show()
    w.settingForm.show()
    sys.exit(app.exec_())


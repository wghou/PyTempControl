# -*- coding: utf-8 -*-

import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow
from WindowApp.MainWindow import Ui_MainWindow
from WindowApp.SetForm import SetForm
from PyQt5.QtCore import *
from Device.Devices import *


class MainForm(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainForm,self).__init__()
        self.devAll = Devices()
        self.setupUi(self)
        self.settingForm = SetForm(self.devAll.tpDevice)
        self.settingForm.setWindowModality(Qt.ApplicationModal)
        self.pushButton_auto.clicked.connect(self._clicked_auto)
        self.pushButton_param.clicked.connect(self._clicked_param)
        self.pushButton_exit.clicked.connect(self._exit_window)

        #
        self.devAll.tpUpdateTickSignal.connect(self._update_tpshow)
        #
        self._set_device()

    def _clicked_auto(self):
        pass

    def _clicked_param(self):
        self.settingForm.show()

    def _set_device(self):
        self.devAll.start_timer()

    def _exit_window(self):
        self.close()

    def _update_tpshow(self, ls):
        _translate = QtCore.QCoreApplication.translate
        if len(ls) != 6:
            return
        else:
            self.label_tempt.setText(_translate("MainWindow", "%.4f" % ls[1]))
            self.label_power.setText(_translate("MainWindow", "%.3f" % ls[3]))
            self.label_fluc.setText(_translate("MainWindow", "%.3f" % ls[5]))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MainForm()
    w.show()
    sys.exit(app.exec_())


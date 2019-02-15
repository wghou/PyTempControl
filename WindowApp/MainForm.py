# -*- coding: utf-8 -*-

import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow
from WindowApp.MainWindow import Ui_MainWindow
from WindowApp.SetForm import SetForm
from WindowApp.AutoListForm import AutoListForm
from WindowApp.CurveForm import CurveForm
from PyQt5.QtCore import *
from Device.Devices import *


class MainForm(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainForm,self).__init__()
        self.devAll = Devices()
        self.setupUi(self)
        self._setForm = SetForm(self.devAll)
        self._setForm.setWindowModality(Qt.ApplicationModal)
        self._autoListForm = AutoListForm(self.devAll)
        self._autoListForm.setWindowModality(Qt.ApplicationModal)
        self._curveForm = CurveForm(self.devAll)

        self._init_key_board()

        #
        self.devAll.tpUpdateTickSignal.connect(self._update_tpshow)
        #
        self._set_device()

    def _init_key_board(self):
        self.pushButton_auto.clicked.connect(lambda: self._autoListForm.show())
        self.pushButton_param.clicked.connect(lambda: self._setForm.show())
        self.pushButton_curve.clicked.connect(lambda: self._curveForm.show())
        self.pushButton_exit.clicked.connect(self._exit_window)

    def _set_device(self):
        self.devAll.tpDevice.reset_port_name('COM3', 2400)
        self.devAll.ryDevice.reset_port_name('COM7', 2400)
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


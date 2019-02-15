# -*- coding: utf-8 -*-

import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QSizePolicy
from WindowApp.AutoListWindow import Ui_AutoListWindow
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtCore import *
from Device.Devices import *


class AutoListForm(QWidget, Ui_AutoListWindow):
    def __init__(self, devall):
        super(AutoListForm,self).__init__()
        self.setupUi(self)
        self._devAll = devall

        self._listModel = QtGui.QStandardItemModel(4, 7)
        self._listModel.setHorizontalHeaderLabels(['温度设定值', '超前调整值', '模糊系数', '比例系数', '积分系数', '功率系数', '编辑'])
        self.tableView.setModel(self._listModel)


if __name__ == '__main__':
    pass

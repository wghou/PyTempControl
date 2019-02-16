# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'CurveWindow.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_CurveWindow(object):
    def setupUi(self, CurveWindow):
        CurveWindow.setObjectName("CurveWindow")
        CurveWindow.resize(523, 473)
        self.pushButton_exit = QtWidgets.QPushButton(CurveWindow)
        self.pushButton_exit.setGeometry(QtCore.QRect(390, 420, 111, 41))
        self.pushButton_exit.setObjectName("pushButton_exit")
        self.groupBox = QtWidgets.QGroupBox(CurveWindow)
        self.groupBox.setGeometry(QtCore.QRect(10, 10, 491, 391))
        self.groupBox.setObjectName("groupBox")

        self.retranslateUi(CurveWindow)
        QtCore.QMetaObject.connectSlotsByName(CurveWindow)

    def retranslateUi(self, CurveWindow):
        _translate = QtCore.QCoreApplication.translate
        CurveWindow.setWindowTitle(_translate("CurveWindow", "Form"))
        self.pushButton_exit.setText(_translate("CurveWindow", "返回主界面"))
        self.groupBox.setTitle(_translate("CurveWindow", "GroupBox"))


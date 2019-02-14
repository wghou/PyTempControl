# -*- coding: utf-8 -*-

import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QWidget, QMessageBox, QMainWindow, QDialog
from WindowApp.ParamSetWindow import Ui_Form
from Device import TemptDevice


class SetForm(QWidget, Ui_Form):
    def __init__(self, tpdev):
        super(SetForm,self).__init__()
        self.setupUi(self)
        self._tpDev = tpdev
        self._tbList = [self.textBrowser_tpSet, self.textBrowser_correct, self.textBrowser_leadAdjust,
                        self.textBrowser_fuzzy, self.textBrowser_ratio, self.textBrowser_int, self.textBrowser_power]
        self._tbEdit = None
        self._install_event_filter()

        self._init_key_board()

        self.pushButton_return.clicked.connect(lambda: self.close())

    def showEvent(self, QShowEvent):
        for i in range(len(self._tbList)):
            self._tbList[i].setText("%.4f" % self._tpDev.tpParam[i])

    def _init_key_board(self):
        self.pushButton_9.clicked.connect(self._bt_9_clicked)

    def _bt_9_clicked(self):
        if self._tbEdit is None:
            QMessageBox.information(self,"警告！", "请先选定设定项 !")
        else:
            txt = self._tbEdit.toPlainText()
            if len(txt) == 1 and txt == '0':
                txt = '9'
            elif len(txt) == 2 and txt == '-0':
                txt = '-9'
            else:
                txt += '9'
            self._tbEdit.setText(txt)

    def _install_event_filter(self):
        for tb in self._tbList:
            tb.installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.FocusIn:
            if obj == self.textBrowser_tpSet:
                self._tbEdit = self.textBrowser_tpSet
            elif obj == self.textBrowser_correct:
                self._tbEdit = self.textBrowser_correct
            elif obj == self.textBrowser_leadAdjust:
                self._tbEdit = self.textBrowser_leadAdjust
            elif obj == self.textBrowser_fuzzy:
                self._tbEdit = self.textBrowser_fuzzy
            elif obj == self.textBrowser_ratio:
                self._tbEdit = self.textBrowser_ratio
            elif obj == self.textBrowser_int:
                self._tbEdit = self.textBrowser_int
            elif obj == self.textBrowser_power:
                self._tbEdit = self.textBrowser_power
            else:
                return QWidget.eventFilter(obj, event)
            return False
        else:
            return QWidget.eventFilter(self, obj, event)



if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = SetForm()
    w.show()
    sys.exit(app.exec_())


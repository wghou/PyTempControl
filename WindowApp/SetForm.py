# -*- coding: utf-8 -*-

import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QWidget, QMessageBox, QMainWindow, QDialog
from WindowApp.ParamSetWindow import Ui_Form
from Device import Devices, TemptDevice
from Utils.TypeAssert import typeassert


class SetForm(QWidget, Ui_Form):
    def __init__(self, devall):
        super(SetForm,self).__init__()
        self.setupUi(self)
        self._devAll = devall  # ss
        self._tbList = [self.textBrowser_tpSet, self.textBrowser_correct, self.textBrowser_leadAdjust,
                        self.textBrowser_fuzzy, self.textBrowser_ratio, self.textBrowser_int, self.textBrowser_power]
        self._tbEdit = self.textBrowser_tpSet
        self._install_event_filter()

        self._init_key_board()

        self._devAll.tpParamUpdateSignal.connect(self._param_read_finished)

    def showEvent(self, QShowEvent):
        for i in range(len(self._tbList)):
            self._tbList[i].setText("%.4f" % self._devAll.tpDevice.tpParam[i])

    def _init_key_board(self):
        self.pushButton_0.clicked.connect(self._bt_0_clicked)
        self.pushButton_1.clicked.connect(self._bt_1_clicked)
        self.pushButton_2.clicked.connect(self._bt_2_clicked)
        self.pushButton_3.clicked.connect(self._bt_3_clicked)
        self.pushButton_4.clicked.connect(self._bt_4_clicked)
        self.pushButton_5.clicked.connect(self._bt_5_clicked)
        self.pushButton_6.clicked.connect(self._bt_6_clicked)
        self.pushButton_7.clicked.connect(self._bt_7_clicked)
        self.pushButton_8.clicked.connect(self._bt_8_clicked)
        self.pushButton_9.clicked.connect(self._bt_9_clicked)
        self.pushButton_pm.clicked.connect(self._bt_ng_clicked)
        self.pushButton_point.clicked.connect(self._bt_point_clicked)
        self.pushButton_back.clicked.connect(self._bt_back_clicked)
        self.pushButton_del.clicked.connect(self._bt_clear_clicked)

        self.pushButton_return.clicked.connect(lambda: self.close())
        self.pushButton_checkParam.clicked.connect(self._bt_checkParam_clicked)
        self.pushButton_setParam.clicked.connect(self._bt_setParam_clicked)


    def _bt_setParam_clicked(self):
        param = [0.0] * 7
        try:
            for i in range(len(self._tbList)):
                txt = self._tbList[i].toPlainText()
                param[i] = float(txt)
        except Exception as ex:
            print(ex)
            QMessageBox.information(self, "警告！", "参数格式错误 !")
            return

        self.tpRt = TemptDevice.TemptComThread()
        self.tpRt.finishSignal.connect(self._param_write_finished)
        self.tpRt.write_tp_param(self._devAll.tpDevice, param, errCnt=False)

    def _param_write_finished(self, ls):
        if ls[0] != TemptDevice.TemptProtocol.ErrTempt.NoError:
            QMessageBox.information(self, "警告！", "参数写入失败 !")
        else:
            QMessageBox.information(self, "警告！", "参数写入成功 !")

    def _bt_checkParam_clicked(self):
        self.tpCk = TemptDevice.TemptComThread()
        self.tpCk.finishSignal.connect(self._param_read_finished)
        self.tpCk.read_tp_param(self._devAll.tpDevice, errCnt=False)

    def _param_read_finished(self, ls):
        for i in range(len(self._tbList)):
            self._tbList[i].setText("%.4f" % ls[1][i])

        if ls[0] != TemptDevice.TemptProtocol.ErrTempt.NoError:
            QMessageBox.information(self, "警告！", "参数读取失败 !")
        else:
            QMessageBox.information(self, "警告！", "参数读取成功 !")

    def _bt_9_clicked(self):
        self._bt_num_clicked(9)

    def _bt_8_clicked(self):
        self._bt_num_clicked(8)

    def _bt_7_clicked(self):
        self._bt_num_clicked(7)

    def _bt_6_clicked(self):
        self._bt_num_clicked(6)

    def _bt_5_clicked(self):
        self._bt_num_clicked(5)

    def _bt_4_clicked(self):
        self._bt_num_clicked(4)

    def _bt_3_clicked(self):
        self._bt_num_clicked(3)

    def _bt_2_clicked(self):
        self._bt_num_clicked(2)

    def _bt_1_clicked(self):
        self._bt_num_clicked(1)

    def _bt_0_clicked(self):
        self._bt_num_clicked(0)

    @typeassert(num=int)
    def _bt_num_clicked(self, num):
        txt = self._tbEdit.toPlainText()
        if len(txt) == 1 and txt == '0':
            txt = '%d' % num
        elif len(txt) == 2 and txt == '-0':
            txt = '-%d' % num
        else:
            txt += '%d' % num
        self._tbEdit.setText(txt)

    def _bt_ng_clicked(self):
        txt = self._tbEdit.toPlainText()
        if len(txt) == 0:
            txt = '-'
        elif txt[0] == '-':
            txt = txt[1:]
        else:
            txt = '-' + txt
        self._tbEdit.setText(txt)

    def _bt_point_clicked(self):
        txt = self._tbEdit.toPlainText()
        if not txt.__contains__('.'):
            if len(txt) == 0:
                txt = '0.'
            elif txt == '-':
                txt = '-0.'
            else:
                txt += '.'
            self._tbEdit.setText(txt)

    def _bt_back_clicked(self):
        txt = self._tbEdit.toPlainText()
        if len(txt) != 0:
            txt = txt[:-1]
        self._tbEdit.setText(txt)

    def _bt_clear_clicked(self):
        self._tbEdit.clear()

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
                return QWidget.eventFilter(self, obj, event)
            return False
        else:
            return QWidget.eventFilter(self, obj, event)


if __name__ == '__main__':
    pass


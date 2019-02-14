# -*- coding: utf-8 -*-


import sys
import threading
import time
from PyQt5 import QtCore
from Utils.TypeAssert import typeassert
from Device.TemptProtocol import TemptProtocol


class TemptDevice(object):
    def __init__(self):
        self._tpDeviceName = None
        self._tpPortName = None
        self._tpDeviceProtocol = TemptProtocol()
        self.tpParam = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.tpParamToSet = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self._tpParamFormat = ('.3f', '.3f', '.3f', '.0f', '.0f', '.0f', '.0f')
        self.tpParamNames = ("设定值    ", "调整值    ", "超前调整值", "模糊系数  ",
                             "比例系数  ", "积分系数  ", "功率系数  ")
        self.tpPowerShow = 0.0
        self.temperatures = list()
        self._temptMaxLen = 1000
        self._tpLocker = threading.Lock()
        # device error count
        self._errDict = {}
        self.clear_err_dict()

    @typeassert(portName=str)
    def setDevicePortName(self, portName):
        """\
        set the port name and check whether the serial port is available
        :param portName: port name
        :return: return True if success
        """
        # if the serial port is not initialized, then create a new RelayProtocol()
        with self._tpLocker:
            # set the port name and baud rate
            confOk = self._tpDeviceProtocol.setPort(portName, 2400)
            # save the port name if success
            if confOk:
                self._tpPortName = portName
            # return the result
            return confOk

    def selfCheck(self):
        """
        check the condition and communication between the pc and T-C board
        :return: error information
        """
        err = TemptProtocol.ErrTempt.NoError
        with self._tpLocker:
            for cmd in TemptProtocol.CmdTempt:
                # read parameters form the T-C board
                err, val = self._tpDeviceProtocol.readData(cmd)
                # if error, break and return the error information
                if err != TemptProtocol.ErrTempt.NoError:
                    break
                if cmd == TemptProtocol.CmdTempt.TempShow:
                    self._addtemperatures(val)
                elif cmd == TemptProtocol.CmdTempt.PowerShow:
                    self.tpPowerShow = val
                else:
                    self.tpParam[cmd] = val
                time.sleep(1)
        return err

    def updateparamtodevice(self, param, errCnt=False):
        """
        update the parameters from the PC to the T-C board
        first write the parameters from the PC to the self.tpParamToSet[]
        then call this function to write the parameter value through serial port
        :param param: T-C board parameters gonna set
        :param errCnt: indicate whether the error information be added into self._errDict
        :return: error information
        """
        err = TemptProtocol.ErrTempt.NoError
        with self._tpLocker:
            # ensure that the formation of the parameter is correct
            if len(param) != len(self.tpParamToSet):
                if errCnt:
                    self._errDict[TemptProtocol.ErrTempt.CodeError] += 1
                return TemptProtocol.ErrTempt.CodeError
            # copy the param to tpParamToSet
            self.tpParamToSet = param
            for cmd in TemptProtocol.CmdTempt:
                if cmd in (TemptProtocol.CmdTempt.TempShow, TemptProtocol.CmdTempt.PowerShow):
                    continue
                if abs(self.tpParam[cmd] - self.tpParamToSet[cmd]) < 10e-5:
                    continue
                err = self._tpDeviceProtocol.writedate(cmd, self.tpParamToSet[cmd])
                if err != TemptProtocol.ErrTempt.NoError:
                    break
                else:
                    self.tpParam[cmd] = self.tpParamToSet[cmd]
                # count the error information
                if errCnt and err != TemptProtocol.ErrTempt.NoError:
                    self._errDict[err] += 1
        return err

    def updateparamfromdevice(self, errCnt=False):
        """\
        update parameters form the T-C board to the PC
        ignore the PowerShow and TemptShow
        :param errCnt: indicate whether the error information be added into self._errDict
        :return: error information, self.tpParam
        """
        err = TemptProtocol.ErrTempt.NoError
        with self._tpLocker:
            for cmd in TemptProtocol.CmdTempt:
                if cmd == TemptProtocol.CmdTempt.PowerShow or cmd == TemptProtocol.CmdTempt.TempShow:
                    continue
                err, val = self._tpDeviceProtocol.readData(cmd)
                if err != TemptProtocol.ErrTempt.NoError:
                    break
                else:
                    self.tpParam[cmd] = val
            # count the error information
            if errCnt and err != TemptProtocol.ErrTempt.NoError:
                self._errDict[err] += 1
        return err, self.tpParam

    def gettempshow(self, errCnt=False):
        """\
        get the temperatureShow from the T-C board
        :param errCnt: indicate whether the error information be added into self._errDict
        :return: error, temptShow
        """
        with self._tpLocker:
            err, val = self._tpDeviceProtocol.readData(TemptProtocol.CmdTempt.TempShow)
            if err == TemptProtocol.ErrTempt.NoError:
                self._addtemperatures(val)
            else:
                if self.temperatures.__len__() > 0:
                    val = self.temperatures[-1]
                else:
                    val = 0.0
            # count the error information
            if errCnt and err != TemptProtocol.ErrTempt.NoError:
                self._errDict[err] += 1
        return err, val

    def getpowershow(self, errCnt=False):
        """\
        get the powerShow from the T-C board
        :param errCnt: indicate whether the error information be added into self._errDict
        :return: error , powerShow
        """
        with self._tpLocker:
            err, val = self._tpDeviceProtocol.readData(TemptProtocol.CmdTempt.PowerShow)
            if err == TemptProtocol.ErrTempt.NoError:
                self.tpPowerShow = val
            else:
                val = self.tpPowerShow
            # count the error information
            if errCnt and err != TemptProtocol.ErrTempt.NoError:
                self._errDict[err] += 1
        return err, val

    @typeassert(cnt=int, crt=float)
    def check_fluc_cnt(self, cnt, crt):
        """\
        check if the fluctuation with the mSec time space satisfies the criteria
        :param cnt: number of temperature value
        :param crt: fluctuation criteria
        :return: result if the fluctuation satisfy the criteria
        """
        flucOk, fluc = self.getfluc(cnt)
        if flucOk:
            return fluc < crt
        else:
            return False

    @typeassert(count=int)
    def getfluccountorless(self, count):
        """\
        calculate the fluctuation with the count-th value of the list
        if the number of values in the list is less than count, then calculate through the entire
        list anyway
        if the number of value in the list is less than 2, then return false
        :param count:
        :return: True/False , fluctuation
        """
        with self._tpLocker:
            if self.temperatures.__len__() < 2:
                return False, -1.0
            elif self.temperatures.__len__() < count:
                return True, max(self.temperatures) - min(self.temperatures)
            else:
                return True, max(self.temperatures[-count:]) - min(self.temperatures[-count:])


    @typeassert(count=int)
    def getfluc(self, count):
        """\
        calculate the fluctuation of the within the last count-th value in the list
        :param count:
        :return: True/False fluctuation
        """
        with self._tpLocker:
            if self.temperatures.__len__() == 0 or self.temperatures.__len__() < count:
                return False, -1.0
            else:
                return True, max(self.temperatures[-count:]) - min(self.temperatures[-count:])

    @typeassert(count=int)
    def _getmaxmintempt(self, count):
        """\
        calculate the max and min value in the last count-th value in the list
        :param count: the max and min value of the last count-th value in the list
        :return: True/False MaxValue MinValue
        """
        if self.temperatures.__len__() == 0 or self.temperatures.__len__() < count:
            return False, 1000.0, -1000.0
        else:
            return True, max(self.temperatures[-count:]), min(self.temperatures[-count:])

    @typeassert(val=float)
    def _addtemperatures(self, val):
        """\
        append value in the end of list temperatures
        if the length of lis temperatures longer than self._temptMaxLen, then del the first one
        of the list temperatures, which keep the length of list no bigger than self._temptMaxLen
        :param val: the temperature value need to be stored
        :return:
        """
        if self.temperatures.__len__() == self._temptMaxLen:
            del self.temperatures[0]
        self.temperatures.append(val)

    def err_dict(self):
        """\
        get the error information dictionary self._errDict
        :return: self._errDict
        """
        return self._errDict

    def clear_err_dict(self):
        """\
        clear the error information in the dictionary self._errDict
        :return: None
        """
        with self._tpLocker:
            for err in TemptProtocol.ErrTempt:
                self._errDict[err] = 0


class TemptComThread(QtCore.QThread):
    finishSignal = QtCore.pyqtSignal(list)

    def __init__(self, parent=None):
        super(TemptComThread, self).__init__(parent)
        self._tpDevice = None
        self._paramToSet = []
        self._errCnt = False
        # thread execute mode,
        # 0: do nothing     1: read param       2: write param
        # 3: read tpShow    4: read pwShow
        self._executeMode = 0

    def read_tp_param(self, tp, errCnt=False):
        """\
        read parameters from the T-C board
        :param tp: tp Device object
        :param errCnt: whether count the error information
        :return: None
        """
        self._tpDevice = tp
        self._executeMode = 1
        self._errCnt = errCnt
        self.start()

    def write_tp_param(self, tp, param, errCnt=False):
        """\
        write parameters to the T-C board
        :param tp: tp Device object
        :param param: the parameter values gonna write to the T-C board
        :param errCnt: whether count the error information
        :return: None
        """
        self._tpDevice = tp
        self._executeMode = 2
        self._errCnt = errCnt
        #
        if len(param) != 7:
            self.finishSignal.emit([TemptProtocol.ErrTempt.CodeError])
            return
        self._paramToSet = param
        self.start()

    def read_tp_show(self, tp, errCnt=False):
        """\
        read temperature show value from the T-C board
        :param tp: tp Device object
        :param errCnt: whether count the error information
        :return: None
        """
        self._tpDevice = tp
        self._executeMode = 3
        self._errCnt = errCnt
        self.start()

    def read_pw_show(self, tp, errCnt=False):
        """
        read the power show value from the T-C board
        :param tp: tp Device object
        :param errCnt: whether count the error information
        :return: None
        """
        self._tpDevice = tp
        self._executeMode = 4
        self._errCnt = errCnt
        self.start()

    def run(self):
        # read parameters form the T-C board
        if self._executeMode == 1:
            err, param = self._tpDevice.updateparamfromdevice(self._errCnt)
            self.finishSignal.emit([err, param])
        # write the parameters to the T-C board
        elif self._executeMode == 2:
            err = self._tpDevice.updateparamtodevice(self._paramToSet, self._errCnt)
            self.finishSignal.emit([err])
        # read the temperatures
        elif self._executeMode == 3:
            err, val = self.gettempshow(self._errCnt)
            self.finishSignal.emit([err, val])
        # read the power value
        elif self._executeMode == 4:
            err, val = self.getpowershow(self._errCnt)
            self.finishSignal.emit([err, val])
        else:
            pass


if __name__ == '__main__':
    tpDevice = TemptDevice()
    conf = tpDevice.setDevicePortName('COM1')
    print('device set port name: %s' % conf)
    err = tpDevice.selfCheck()
    print('device self check: %s' %err)
    err, prm = tpDevice.updateparamfromdevice(True)
    print('update param from device: %s   err: %s' % (prm,err))
    print('errdic: %s' % tpDevice.err_dict())
    prm = [0.0]*7
    err = tpDevice.updateparamtodevice(param=prm, errCnt=True)
    print('update param from device: %s' % err)
    print('errdic: %s' % tpDevice.err_dict())
    err, val = tpDevice.gettempshow(errCnt=True)
    print('the temperature show is: %f   err: %s' % (val, err))
    print('errdic: %s' % tpDevice.err_dict())
    err, val = tpDevice.getpowershow(errCnt=True)
    print('the power show is: %f   err: %s' % (val, err))
    print('errdic: %s' % tpDevice.err_dict())

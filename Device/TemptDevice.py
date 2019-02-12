# -*- coding: utf-8 -*-


import sys
import threading
import time
from Utils.TypeAssert import typeassert
from Device.TemptProtocol import TemptProtocol


class TemptDevice(object):
    def __init__(self):
        self._tpDeviceName = None
        self._tpPortName = None
        self._tpDeviceProtocol = None
        self.tpParam = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        self.tpParamToSet = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        self._tpParamFormat = ['.3f', '.3f', '.3f', '.0f', '.0f', '.0f', '.0f']
        self.tpParamNames = ["设定值    ", "调整值    ", "超前调整值", "模糊系数  ", "比例系数  ", "积分系数  ", "功率系数  "]
        self.tpPowerShow = 0.0
        self.temperatures = list()
        self._temptMaxLen = 1000
        self.readTemptIntervalMsec = 1000
        self._tpLocker = threading.Lock()

    @typeassert(portName=str)
    def setdeviceportname(self, portName):
        """\
        set the port name and check whether the serial port is available
        :param portName: port name
        :return: return True if success
        """
        confOk = False
        # if the serial port is not initialized, then create a new RelayProtocol()
        with self._ryLocker:
            if self._tpDeviceProtocol is None:
                self._tpDeviceProtocol = TemptProtocol(portName, 2400)
            # set the port name and baud rate
            confOk = self._tpDeviceProtocol.setport(portName, 2400)
            # save the port name if success
            if confOk:
                self._tpPortName = portName
            # return the result
            return confOk

    def selfcheck(self):
        """
        check the condition and communication between the pc and T-C board
        :return: error information
        """
        err = TemptProtocol.ErrTempt.NoError
        with self._tpLocker:
            for cmd in TemptProtocol.CmdTempt:
                # read parameters form the T-C board
                err, val = self._tpDeviceProtocol.readdata(cmd)
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

    def updateparamtodevice(self):
        """
        update the parameters from the PC to the T-C board
        first write the parameters from the PC to the self.tpParamToSet[]
        then call this function to write the parameter value through serial port
        :return: error information
        """
        err = TemptProtocol.ErrTempt.NoError
        with self._tpLocker:
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
        return err

    def updateparamfromdevice(self):
        """\
        update parameters form the T-C board to the PC
        ignore the PowerShow and TemptShow
        :return: error information
        """
        err = TemptProtocol.ErrTempt.NoError
        with self._tpLocker:
            for cmd in TemptProtocol.CmdTempt:
                if cmd == TemptProtocol.CmdTempt.PowerShow or cmd == TemptProtocol.CmdTempt.TempShow:
                    continue
                err, val = self._tpDeviceProtocol.readdata(cmd)
                if err != TemptProtocol.ErrTempt.NoError:
                    break
                else:
                    self.tpParam[cmd] = val
        return err

    def gettempshow(self):
        """\
        get the temperatureShow from the T-C board
        :return: error, temptShow
        """
        err = TemptProtocol.ErrTempt.NoError
        val = 0.0
        with self._tpLocker:
            err, val = self._tpDeviceProtocol.readdata(TemptProtocol.CmdTempt.TempShow)
            if err == TemptProtocol.ErrTempt.NoError:
                self._addtemperatures(val)
            else:
                if self.temperatures.__len__() > 0:
                    val = self.temperatures[-1]
                else:
                    val = 0.0
        return err, val

    def getpowershow(self):
        """\
        get the powerShow from the T-C board
        :return: error , powerShow
        """
        err = TemptProtocol.ErrTempt.NoError
        val = 0.0
        with self._tpLocker:
            err, val = self._tpDeviceProtocol.readdata(TemptProtocol.CmdTempt.PowerShow)
            if err == TemptProtocol.ErrTempt.NoError:
                self.tpPowerShow = val
            else:
                val = self.tpPowerShow
            return err, val

    @typeassert(mSec=int, crt=float)
    def checkflucmsec(self, mSec, crt):
        """\
        check if the fluctuation with the mSec time space satisfies the criteria
        :param mSec: time space
        :param crt: fluctuation criteria
        :return: result if the fluctuation satisfy the criteria
        """
        flucOk, fluc = self.getfluc(int(mSec/self.readTemptIntervalMsec))
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


if __name__ == '__main__':
    val = [1, 2, 3]
    print(val[-2:])

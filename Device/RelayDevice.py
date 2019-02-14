# -*- coding: utf-8 -*-


import threading
import time
from PyQt5 import QtCore
from Utils.TypeAssert import typeassert
from Device.RelayProtocol import RelayProtocol


class RelayDevice(object):
    def __init__(self):
        self._ryDeviceName = None
        self._ryPortName = None
        self._ryDeviceProtocol = None
        self.ryStatus = [True, False, False, False,
                         False, False, False, False,
                         False, False, False, False,
                         False, False, False, False]
        self._ryStatusToSet = [True, False, False, False,
                         False, False, False, False,
                         False, False, False, False,
                         False, False, False, False]
        self._ryLocker = threading.Lock()
        # device error count
        self._errDict = {}
        self.clear_err_dict()

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
            if self._ryDeviceProtocol is None:
                self._ryDeviceProtocol = RelayProtocol(portName, 9600)
            # set the port name and baud rate
            confOk = self._ryDeviceProtocol.setport(portName, 9600)
            # save the port name if success
            if confOk:
                self._ryPortName = portName
            # return the result
            return confOk

    @typeassert(stToSet=list, errCnt=bool)
    def updatestatustodevice(self, stToSet, errCnt=False):
        """\
        update the relay status to the relay device
        every time we wanna set relay status, we write the relay status in the ryStatusToSet.
        regularly call this function, and it checks if the ryStatus equals to the ryStatusToSet.
        if different, it means that the relay status need to be update. and the new relay status
        in the ryStatusToSet is written to the relay device. if success, update the relay status
        in the ryStatus
        :param stToSet: the relay status gonna set
        :return: success of failed
        """
        err = RelayProtocol.ErrRelay.NoError
        # lock
        with self._ryLocker:
            # copy the status to self._ryStatusToSet[]
            for i in range(len(stToSet)):
                self._ryStatusToSet[i] = stToSet[i]
            # for each cmd in the RelayProtocol.CmdRelay, check if the relay status need to be update
            # if the ryStatus[cmd] != ryStatusToSet[cmd], it means that the relay status need to be update
            for cmd in RelayProtocol.CmdRelay:
                if self.ryStatus[cmd] == self.ryStatusToSet[cmd]:
                    continue
                err = self._ryDeviceProtocol.writerelaystatus(cmd, self.ryStatusToSet[cmd])
                time.sleep(20/1000)
                if err == RelayProtocol.ErrRelay.NoError:
                    self.ryStatus[cmd] = self.ryStatusToSet[cmd]
                else:
                    break
            if errCnt and err != RelayProtocol.ErrRelay.NoError:
                self._errDict[err] += 1
        # return the err information. success of failed
        return err, self.ryStatus

    def err_dict(self):
        return self._errDict

    def clear_err_dict(self):
        with self._ryLocker:
            for err in RelayProtocol.ErrRelay:
                self._errDict[err] = 0


class RelayComThread(QtCore.QThread):
    """
    communicate with relay device in a new thread
    after finish, emit a signal with parameter RelayProtocol.ErrRelay
    """
    # finish signal
    finishSignal = QtCore.pyqtSignal(list)

    def __init__(self, parent=None):
        super(RelayComThread, self).__init__(parent)
        self._rydevice = None
        self._stToSet = []
        self._errCnt = False

    def set_ry_status(self, ry, st, errCnt=False):
        self._rydevice = ry
        self._stToSet = st
        self._errCnt = errCnt
        self.start()

    def run(self):
        err, ryst = self._rydevice.updatestatustodevice(self._stToSet, self._errCnt)
        self.finishSignal.emit([err, ryst])



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
        self.ryStatusToSet = [True, False, False, False,
                         False, False, False, False,
                         False, False, False, False,
                         False, False, False, False]
        self._ryLocker = threading.Lock()

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

    def updatestatustodevice(self):
        """\
        update the relay status to the relay device
        every time we wanna set relay status, we write the relay status in the ryStatusToSet.
        regularly call this function, and it checks if the ryStatus equals to the ryStatusToSet.
        if different, it means that the relay status need to be update. and the new relay status
        in the ryStatusToSet is written to the relay device. if success, update the relay status
        in the ryStatus
        :return: success of failed
        """
        err = RelayProtocol.ErrRelay.NoError
        # lock
        with self._ryLocker:
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
        # return the err information. success of failed
        return err


class RelayComThread(QtCore.QThread):
    """
    communicate with relay device in a new thread
    after finish, emit a signal with parameter RelayProtocol.ErrRelay
    """
    # finish signal
    finishSignal = QtCore.pyqtSignal(RelayProtocol.ErrRelay)

    @typeassert(rydevice=RelayDevice)
    def __init__(self, rydevice, parent=None):
        print('init th')
        super(RelayComThread, self).__init__(parent)
        self._rydevice = rydevice

    def run(self):
        print('run')
        err = RelayProtocol.ErrRelay.NoError
        err = self._rydevice.updatestatustodevice()
        self.finishSignal.emit(err)


# test
def _set_rystatus_end(self, err):
    print('end')
    print(err)

import os
if __name__ == '__main__':
    dev = RelayDevice()
    dev.setdeviceportname('COM0')
    dev.ryStatusToSet[RelayProtocol.CmdRelay.Circle] = True
    ryThread = RelayComThread(dev)
    ryThread.finishSignal.connect(_set_rystatus_end)
    print('start')
    ryThread.start()
    os.system("pause")

# -*- coding: utf-8 -*-


import serial
from enum import Enum, unique
from Utils.TypeAssert import typeassert
import time


@unique
class Cmd_t(Enum):
    TempSet =0
    TempCorrect = 1
    LeadAdjust = 2
    Fuzzy = 3
    Ratio = 4
    Integral = 5
    Power = 6
    TempShow = 7
    PowerShow = 8


@unique
class Err_t(Enum):
    NoError = 0
    NotInRange = 1
    UnknownCmd = 2
    IncompleteCmd = 3
    BCCError = 4
    ComError = 5
    CodeError = 6


#Err_t = Enum('NoErr', 'NotInRange', 'UnknownCmd', 'IncompleteCmd', 'BCCError', 'ComError', 'CodeError')
#Cmd_t = Enum('TempSet', 'TempCorrect', 'LeadAdjust', 'Fuzzy', 'Ratio', 'Integral', 'Power', 'TempShow', 'PowerShow')


_intervalOfWR = 20

_errorWords = ('A','B', 'C', 'D')
_errorFlag = 'E'
_cmdHead_W = '@35W'
_cmdHead_R = '@35R'
_cmdWords = ('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I' )
_cmdFormats = ('.3f', '.3f', '.3f', '.0f', '.0f', '.0f', '.0f', '.4f', '.0f')
_cmdFinish = ':'
_cmdEnd = '\r'
_cmdRW = ('w', 'w', 'w', 'w', 'w', 'w', 'w', 'r', 'r')


class TempProtocol(object):
    def __init__(self, Port='COM3'):
        self._sPort = None
        self.avilable = False
        self.data = None

    @typeassert(portName = str)
    def setport(self, portname):
        try:
            self._sPort = serial.Serial()
            self._sPort.port = portname
            self._sPort.baudrate = 2400
            self._sPort.bytesize = serial.EIGHTBITS
            self._sPort.timeout = 250
            self._sPort.stopbits = serial.STOPBITS_ONE
            self._sPort.parity = serial.PARITY_NONE
            self._sPort.open()
            if self._sPort.isOpen():
                self.avilable = False
                return False
            else:
                self.avilable = True
                return True
        except(serial.SerialException):
            self.avilable = False
            return False

    @typeassert(cmd = Cmd_t, val = (int, float))
    def senddata(self, cmd, val):
        # can not send TempShow and PowerShow
        assert cmd != Cmd_t.TempShow
        assert cmd != Cmd_t.PowerShow
        if _cmdRW[cmd] != 'w':
            return Err_t.CodeError
        command = self._constructcommand(cmd, val, True)
        try:
            if not self._sPort.isOpen():
                self._sPort.open()
            self._sPort.write((command+'\r\n').encode())
            time.sleep(_intervalOfWR/1000)
            data = self._sPort.readline()
            self._sPort.close()
        except:
            pass
            try:
                self._sPort.close()
            except:
                pass
            return Err_t.ComError
        return self._iserr(data)

    def readdata(self, cmd):
        pass

    def _iserr(self, cmd):
        err = Err_t.NoError
        if cmd[3] == _errorFlag:
            try:
                errindex = _errorWords.index(cmd[4])
                err = Err_t(errindex+1)
            except:
                err = Err_t.UnknownCmd
        return err

    @typeassert(cmdname=Cmd_t, val=(int,float), W_R=bool)
    def _constructcommand(self, cmdname, val, W_R):
        command = None
        # check param format
        if W_R:
            command += _cmdHead_W
            command += _cmdWords[cmdname]
            command += '{0:{1}}'.format(val, _cmdFormats[cmdname])
            command += _cmdFinish
            command += self._bcccal(command, False)
            command += _cmdEnd
        else:
            command += _cmdHead_R
            command += _cmdWords[cmdname]
            command += _cmdFinish
            command += self._bcccal(command, False)
            command += _cmdEnd
        return command

    @typeassert(cmd=str, ifcal=bool)
    def _bcccal(self, cmd, ifcal=False):
        bcc = None
        if(ifcal):
            pass
        else:
            bcc = ''
        return bcc

    @typeassert(cmd=str, ifchk=bool)
    def _checkbcc(self, cmd, ifchk=False):
        pass
        return True


@typeassert(x=int, y=(int, float))
def test(x, y):
    print(x)
    print(y)

if __name__ == '__main__':
    val = 10.345
    fmt = '.0f'
    strVal = '{0:{1}}'.format(val, fmt)
    strVal += 'ss'
    print(strVal)
    test(1,2)
    test(1,2.0)
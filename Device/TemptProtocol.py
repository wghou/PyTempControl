# -*- coding: utf-8 -*-


import serial
from enum import Enum, unique

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
_cmdFormats = ('0.000', '0.000', '0.000', '0', '0', '0', '0', '0.0000', '0')
_cmdFinish = ':'
_cmdEnd = '\r'
_cmdRW = ('w', 'w', 'w', 'w', 'w', 'w', 'w', 'r', 'r')


class TempProtocol(object):
    def __init__(self, Port='COM3'):
        self._sPort = None
        self.avilable = False
        self.data = None

    def setport(self, portName):
        try:
            self._sPort = serial.Serial()
            self._sPort.port = portName
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

    def senddata(self, cmd, val):
        if cmd not in Cmd_t:
            raise ValueError("Not a valid SendData Cmd: {!r}".format(cmd))
        if not isinstance(val, float):
            raise TypeError('bad operand type')
        assert cmd != Cmd_t.TempShow
        assert cmd != Cmd_t.PowerShow
        if _cmdRW[cmd] != 'w':
            return Err_t.CodeError


    def _constructcommand(self, cmdName, val, W_R):
        command = None
        # check param format
        if W_R:
            command +=_cmdHead_W
            command += _cmdWords[cmdName]
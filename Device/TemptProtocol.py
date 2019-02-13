# -*- coding: utf-8 -*-


import serial
from enum import IntEnum, unique
from Utils.TypeAssert import typeassert
import time


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


class TemptProtocol(object):
    """\
    The temperature control board communicate protocol class.
    Read and Write parameters from T-C board through serial port.
    """
    def __init__(self, portName, baudRate=2400):
        """\
                Init of TemptProtocol class. If failed to open the named serial port,
                then set the self.available False
                :param portName: serial port name
                :param baudRate: baud rate of the serial port
                """
        self.available = False
        self.data = None
        # create and connect a serial port with port name and baud rate
        # if failed, set the indicator self.available False
        self._sPort = serial.Serial(portName, baudRate)
        try:
            self._sPort.open()
            if self._sPort.isOpen():
                self.available = True
            else:
                self.available = False
            self._sPort.close()
        except serial.SerialException as e:
            self.available = False

    @unique
    class CmdTempt(IntEnum):
        """\
        Command used to read/write parameters from T-C board.
        """
        TempSet = 0
        TempCorrect = 1
        LeadAdjust = 2
        Fuzzy = 3
        Ratio = 4
        Integral = 5
        Power = 6
        TempShow = 7
        PowerShow = 8

    @unique
    class ErrTempt(IntEnum):
        """\
        Error when read/write parameters from T-C board.
        """
        NoError = 0
        NotInRange = 1
        UnknownCmd = 2
        IncompleteCmd = 3
        BCCError = 4
        ComError = 5
        CodeError = 6

    @typeassert(portName=str, baudRate=int)
    def setport(self, portName, baudRate=2400):
        """\
        reset the port name and baud rate, no matter the serial port is available or unavailable
        :param portName: the port name
        :param baudRate: the baud rate
        :return: return True if the serial is OK, otherwise return False
        """
        # try to close the serial port if necessary
        try:
            if self._sPort.isOpen():
                self._sPort.close()
        finally:
            pass
        # reset the serial port
        try:
            self._sPort.port = portName
            self._sPort.baudrate = baudRate
            self._sPort.open()
            if self._sPort.isOpen():
                self.available = False
                return False
            else:
                self.available = True
                return True
        except serial.SerialException as e:
            self.available = False
            return False
        return self.available

    @typeassert(cmd = CmdTempt, val = (int, float))
    def senddata(self, cmd, val):
        """\
        send data (val) to the T-C board according to the cmd
        :param cmd: cmd which indicates the parameter
        :param val: the value of the parameter
        :return: ErrTempt.NoError if success, otherwise return error information
        """
        # if the serial port is un-available
        if not self.available:
            return self.ErrTempt.ComError
        # can not send TempShow and PowerShow
        assert cmd != self.CmdTempt.TempShow
        assert cmd != self.CmdTempt.PowerShow
        # assert the parameter can be write-able
        if _cmdRW[cmd] != 'w':
            return self.ErrTempt.CodeError
        # construct the command
        command = self._constructcommand(cmd, val, True)
        try:
            if not self._sPort.isOpen():
                self._sPort.open()
            # write the command through the serial port
            self._sPort.write((command+'\r\n').encode())
            # wait a while and read the data comes back form the T-C board
            time.sleep(_intervalOfWR/1000)
            data = self._sPort.readline()
            self._sPort.close()
        # serial exception, return error information
        except serial.SerialException as e:
            try:
                self._sPort.close()
            except serial.SerialException as ex:
                pass
            return self.ErrTempt.ComError
        # check the data correction
        return self._iserr(data)

    @typeassert(cmd=CmdTempt)
    def readdata(self, cmd):
        """\
        read data (val) from the T-C board according to the cmd
        :param cmd: command indicates the parameter read from the T-C board
        :return: error information and the parameter value
        """
        err = self.ErrTempt.NoError
        val = 0.0
        # if the serial port is un-available
        if not self.available:
            return self.ErrTempt.ComError, val
        # construct the command
        command = self._constructcommand(cmd, 0.0, False)
        try:
            if not self._sPort.isOpen():
                self._sPort.open()
            # write the command through the serial port
            self._sPort.write((command + '\r\n').encode())
            # wait a while and read the data comes back form the T-C board
            time.sleep(_intervalOfWR / 1000)
            data = self._sPort.readline()
            self._sPort.close()
        # serial exception, return error information
        except serial.SerialException as e:
            try:
                self._sPort.close()
            except serial.SerialException as ex:
                pass
            return self.ErrTempt.ComError, val
        # check the data correction
        err = self._iserr(cmd)
        if err != self.ErrTempt.NoError:
            return err, val
        # parse the parameter value from the string returned
        else:
            try:
                val = float(data[5:])
            except Exception as e:
                val = 0.0
                return self.ErrTempt.BCCError, val
            return self.ErrTempt.NoError, val

    @typeassert(data=str)
    def _iserr(self, data):
        """\
        check if the data returned from the T-C board contains error information
        :param data: the data string returned from the T-C board
        :return: error information if necessary
        """
        err = self.ErrTempt.NoError
        if data[3] == _errorFlag:
            try:
                errindex = _errorWords.index(data[4])
                err = self.ErrTempt(errindex+1)
            except:
                err = self.ErrTempt.UnknownCmd
        return err

    @typeassert(cmdName=CmdTempt, val=(int,float), W_R=bool)
    def _constructcommand(self, cmdName, val, W_R):
        """\
        construct the complete command through the cmdName and val
        :param cmdName: the abbreviate cmd name
        :param val: the parameter value
        :param W_R: command of write or read, True means write, False means read
        :return: return the complete command
        """
        command = None
        # check param format
        if W_R:
            command += _cmdHead_W
            command += _cmdWords[cmdName]
            command += '{0:{1}}'.format(val, _cmdFormats[cmdName])
            command += _cmdFinish
            command += self._bcccal(command, False)
            command += _cmdEnd
        else:
            command += _cmdHead_R
            command += _cmdWords[cmdName]
            command += _cmdFinish
            command += self._bcccal(command, False)
            command += _cmdEnd
        return command

    @typeassert(cmd=str, ifcal=bool)
    def _bcccal(self, cmd, ifcal=False):
        """\
        bcc value calculation
        :param cmd: the complete command string
        :param ifcal: if calculate or not
        :return: return the command with bcc value attached at the back
        """
        bcc = None
        if(ifcal):
            pass
        else:
            bcc = ''
        return bcc

    @typeassert(cmd=str, ifchk=bool)
    def _checkbcc(self, cmd, ifchk=False):
        """\
        bcc correction check
        :param cmd: the complete command with bcc valued attached at the back
        :param ifchk: if check or not
        :return: return the bcc check result
        """
        pass
        return True


if __name__ == '__main__':
    sPort = TemptProtocol('COM1')
    err, val = sPort.readdata(TemptProtocol.CmdTempt.TempShow)
    print("The tempShow is: %f and error information is: %s" % (val, err))
    err = sPort.senddata(TemptProtocol.CmdTempt.Power, 10.0)
    print('The Power value %f is send to the T-C board, and the error information is: %s' % (10.0, err))

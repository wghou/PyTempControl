import serial
from enum import IntEnum, unique
from Utils.TypeAssert import typeassert
import time
import operator


_intervalOfWR = 20
_cmdDeviceAddr = b'0xFE'
_cmdOrder = (b'0x01', b'0x05', b'0x15')
_cmdRelayAddr = (b'0x0000', b'0x0001', b'0x0002', b'0x0003',
                 b'0x0004', b'0x0005',b'0x0006', b'0x0007',
                 b'0x0008', b'0x0009', b'0x000A', b'0x000B',
                 b'0x000C', b'0x000D', b'0x000E', b'0x000F' )
_cmdRelayOnOff = (b'0xff00', b'0x0000')


class RelayProtocol(object):
    """\
    The Relay device communicate protocol class.
    Read and Set relay device status through serial port.
    """
    def __init__(self, portName, baudRate=9600):
        """\
        Init of RelayProtocol class. If failed to open the named serial port,
        then set the self.available False
        :param portName: serial port name
        :param baudRate: baud rate of the serial port
        """
        self.available = False
        self.data = None
        # create and connect a serial port with port name and baud rate
        # if failed, set the indicator self.available False
        self._sPort = serial.Serial()
        try:
            self._sPort.baudrate = baudRate
            self._sPort.name = portName
            self._sPort.open()
            if self._sPort.isOpen():
                self.available = True
            else:
                self.available = False
            self._sPort.close()
        except serial.SerialException as e:
            self.available = False

    @unique
    class CmdRelay(IntEnum):
        """\
        Command used to read/set the relay device.
        """
        Elect = 0
        MainHeat = 1
        Cool = 2
        Circle = 3

    @unique
    class ErrRelay(IntEnum):
        """\
        Error when read/set relay device status
        """
        NoError = 0
        CRCError = 1
        ComError = 2
        CodeError = 3

    @typeassert(portName=str, baudRate=int)
    def setport(self, portName, baudRate=9600):
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
            self._sPort.name = portName
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
            print('Port is un available')
            return False
        return self.available

    @typeassert(cmd=CmdRelay, status=bool)
    def writerelaystatus(self, cmd, status):
        """
        set relay status according to the cmd and status
        :param cmd: cmd indicates which relay gonna set
        :param status: status indicate the relay status to set
        :return: return error information if failed
        """
        # if the serial port is un-available
        if not self.available:
            return self.ErrRelay.ComError
        # construct the complete command to write relay status
        command = bytearray(8)
        dataBack = bytearray(8)
        command[0] = _cmdDeviceAddr
        command[1] = _cmdOrder[1]
        command[2] = bytes(_cmdRelayAddr[cmd] >> 8 & b'0x00FF')
        command[3] = bytes(_cmdRelayAddr[cmd] & b'0x00FF')
        if status:
            command[4] = b'0xFF'
        else:
            command[4] = b'0x00'
        command[5] = b'0x00'
        # calculate the CRC
        self._gencrc16(command)
        try:
            if not self._sPort.isOpen():
                self._sPort.open()
            # write the command through the serial port
            self._sPort.write(command)
            # wait a while and read the data comes back form the T-C board
            time.sleep(_intervalOfWR/1000)
            dataBack = self._sPort.read(dataBack.__len__())
            self._sPort.close()
        # serial exception, return error information
        except serial.SerialException as e:
            try:
                self._sPort.close()
            except serial.SerialException as ex:
                pass
            return self.ErrRelay.ComError
        # check the correction of data return
        if not operator.eq(command, dataBack):
            return self.ErrRelay.CRCError
        # set correctly
        return self.ErrRelay.NoError

    def readallrelaystatus(self):
        status = bytearray(8)
        # if the serial port is un-available
        if not self.available:
            return self.ErrRelay.ComError, status
        # construct the complete command to write relay status
        command = bytearray(8)
        dataBack = bytearray(8)
        command[0] = _cmdDeviceAddr
        command[1] = _cmdOrder[0]
        command[2] = b'0x00'
        command[3] = b'0x00'
        command[4] = b'0x00'
        command[5] = b'0x10'
        # calculate the CRC
        self._gencrc16(command)
        try:
            if not self._sPort.isOpen():
                self._sPort.open()
            # write the command through the serial port
            self._sPort.write(command)
            # wait a while and read the data comes back form the T-C board
            time.sleep(_intervalOfWR / 1000)
            dataBack = self._sPort.read(dataBack.__len__())
            self._sPort.close()
        # serial exception, return error information
        except serial.SerialException as e:
            try:
                self._sPort.close()
            except serial.SerialException as ex:
                pass
            return self.ErrRelay.ComError, status
        # check the correction of data return
        crc = dataBack[5:6]
        self._gencrc16(dataBack)
        if not operator.eq(crc, dataBack[5:6]):
            return self.ErrRelay.CRCError, status
        # read correctly
        # bug wghou 20190212
        # i do not know if the order of relay status is correctly
        status[0] = dataBack[4]
        status[1] = dataBack[3]
        return self.ErrRelay.NoError, status

    @typeassert(command=bytearray)
    def _gencrc16(self, command):
        """\
        calculate the CRC code of command[0:-2] and save it in command[-2:-1]
        :param command: the data used to calculate the CRC
        :return: if calculated, then return True
        """
        _len = bytearray.__len__(command)
        if _len < 2:
            return False
        # calculate the CRC
        xda = b'0xFFFF'
        xdapoly = b'0xA001'
        command_sub = command[0:-2]
        for dt in command_sub:
            xda ^= dt
            for j in range(8):
                xdabit = xda & b'0x01'
                xda >>= 1
                if xdabit == 1:
                    xda ^= xdapoly
        command[-2] = bytes(xda & b'0xff')
        command[-1] = bytes(xda >> 8)
        return True

if __name__ == '__main__':
    val = bytearray(8)
    print(bytearray.__len__(val))
    print(val)
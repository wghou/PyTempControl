import serial
from enum import IntEnum, unique
from Utils.TypeAssert import typeassert
import time
import operator


_intervalOfWR = 20
_cmdDeviceAddr = 0xFE
_cmdOrder = [0x01, 0x05, 0x15]
_cmdRelayAddr = [0x0000, 0x0001, 0x0002, 0x0003,
                 0x0004, 0x0005, 0x0006, 0x0007,
                 0x0008, 0x0009, 0x000A, 0x000B,
                 0x000C, 0x000D, 0x000E, 0x000F]
_cmdRelayOnOff = [0xff00, 0x0000]


class RelayProtocol(object):
    """\
    The Relay device communicate protocol class.
    Read and Set relay device status through serial port.
    """
    def __init__(self):
        """\
        Init of RelayProtocol class. If failed to open the named serial port,
        then set the self.available False
        """
        self.available = False
        # create and connect a serial port with port name and baud rate
        # if failed, set the indicator self.available False
        self._sPort = serial.Serial()

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

    @typeassert(portname=str, baudrate=int)
    def set_port(self, portname, baudrate=9600):
        """\
        reset the port name and baud rate, no matter the serial port is available or unavailable
        :param portname: the port name
        :param baudrate: the baud rate
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
            self._sPort.port = portname
            self._sPort.baudrate = baudrate
            self._sPort.timeout = 0.2
            self.available = True
        except serial.SerialException as e:
            self.available = False
            print(e)
        return self.available

    @typeassert(cmd=CmdRelay, status=bool)
    def write_relay_status(self, cmd, status):
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
        command[0] = _cmdDeviceAddr
        command[1] = _cmdOrder[1]
        command[2] = _cmdRelayAddr[cmd] >> 8 & 0x00FF
        command[3] = _cmdRelayAddr[cmd] & 0x00FF
        if status:
            command[4] = 0xFF
        else:
            command[4] = 0x00
        command[5] = 0x00
        # calculate the CRC
        self._gen_crc16(command)
        try:
            if not self._sPort.isOpen():
                self._sPort.open()
            # write the command through the serial port
            self._sPort.write(command)
            # wait a while and read the data comes back form the T-C board
            time.sleep(_intervalOfWR/1000)
            dataBack = bytearray(self._sPort.read(8))
            self._sPort.close()
        # serial exception, return error information
        except serial.SerialException as e:
            try:
                self._sPort.close()
            except serial.SerialException as ex:
                pass
            return self.ErrRelay.ComError
        # check the correction of data return
        if len(dataBack) != 8:
            return self.ErrRelay.ComError
        if not operator.eq(command, dataBack):
            return self.ErrRelay.CRCError
        # set correctly
        return self.ErrRelay.NoError

    def read_all_relay_status(self):
        status = bytearray(8)
        # if the serial port is un-available
        if not self.available:
            return self.ErrRelay.ComError, status
        # construct the complete command to write relay status
        command = bytearray(8)
        command[0] = _cmdDeviceAddr
        command[1] = _cmdOrder[0]
        command[2] = 0x00
        command[3] = 0x00
        command[4] = 0x00
        command[5] = 0x10
        # calculate the CRC
        self._gen_crc16(command)
        try:
            if not self._sPort.isOpen():
                self._sPort.open()
            # write the command through the serial port
            self._sPort.write(command)
            # wait a while and read the data comes back form the T-C board
            time.sleep(_intervalOfWR / 1000)
            dataBack = bytearray(self._sPort.read(8))
            self._sPort.close()
        # serial exception, return error information
        except serial.SerialException as e:
            try:
                self._sPort.close()
            except serial.SerialException as ex:
                pass
            return self.ErrRelay.ComError, status
        # check the correction of data return
        if len(dataBack) != 8:
            return self.ErrRelay.ComError, status
        crc = dataBack[5:6]
        self._gen_crc16(dataBack)
        if not operator.eq(crc, dataBack[5:6]):
            return self.ErrRelay.CRCError, status
        # read correctly
        # bug wghou 20190212
        # i do not know if the order of relay status is correctly
        status[0] = dataBack[4]
        status[1] = dataBack[3]
        return self.ErrRelay.NoError, status

    @typeassert(command=bytearray)
    def _gen_crc16(self, command):
        """\
        calculate the CRC code of command[0:-2] and save it in command[-2:-1]
        :param command: the data used to calculate the CRC
        :return: if calculated, then return True
        """
        _len = bytearray.__len__(command)
        if _len < 2:
            return False
        # calculate the CRC
        xda = 0xFFFF
        xdapoly = 0xA001
        command_sub = command[0:-2]
        for dt in command_sub:
            xda ^= dt
            for j in range(8):
                xdabit = xda & 0x01
                xda >>= 1
                if xdabit == 1:
                    xda ^= xdapoly
        command[-2] = xda & 0xff
        command[-1] = xda >> 8
        return True

if __name__ == '__main__':
    sPort = RelayProtocol()
    suc = sPort.set_port('COM2')
    print('set port: %s' % suc)
    err = sPort.write_relay_status(RelayProtocol.CmdRelay.Elect, True)
    print('set relay status: %s' % err)
    err, st = sPort.read_all_relay_status()
    print('read all relay status: %s   err: %s' % (st, err))

# -*- coding: utf-8 -*-


import threading
import time
from PyQt5 import QtCore
from transitions import Machine
from Utils.TypeAssert import typeassert
from Device.DevivceParameter import StatesEnum, TemptPointStruct, ThresholdParamStruct
from Device.TemptDevice import TemptDevice, TemptProtocol
from Device.RelayDevice import RelayProtocol, RelayDevice


class Devices(object):

    States = ['start', 'temptUp', 'temptDown', 'control', 'stable',
              'measure', 'stop', 'idle', 'undefined']
    Triggers = ['startAutoStep', 'timerTick', 'nextTemptPoint', 'nextTemptPoint'
                'startControl', 'achieveSteady', 'startMeasure',
                'suspendAutoControl', 'finishAll', 'forceStop', 'uindefinedOccur']

    # when auto control, the control flow enter a new state
    # emit([stateName])
    controlStateChangedSignal = QtCore.pyqtSignal(list)
    # when auto control, the relay device status changed
    # emit([err, st])
    ryStatusUpdateSignal = QtCore.pyqtSignal(list)
    # when the temperature parameters are updated into the T-C board
    # emit(err, param])
    tpParamUpdateSignal = QtCore.pyqtSignal(list)
    # in every tick, the temperature and power are updated from the T-C board
    # emit([errT, tp, errP, p])
    tpUpdateTickSignal = QtCore.pyqtSignal(list)
    # check error in every tick
    tpErrorOccurTickSignal = QtCore.pyqtSignal(list)

    @typeassert(name=str)
    def __init__(self, name='Device'):
        # tempt parameters
        # relay device
        self.ryDevice = RelayDevice()
        # temperature control device
        self.tpDevice = TemptDevice()
        # whether perform auto control
        self.autoControl = False
        # temperature list
        self.temptPointList = []
        # current temperature control state
        self.currentTemptPointState = TemptPointStruct()
        # threading lock
        self.stepLocker = threading.Lock()
        # some parameters
        self.thrParam = ThresholdParamStruct()

        # state machine
        self.name = name
        self._machine = None
        self._init_machine()

        self._timer = threading.Timer(self.thrParam.tpUpdateInterval, self._timer_tick, [self.thrParam.tpUpdateInterval])

    def _init_machine(self):
        self._machine = Machine(model=self, states=Devices.States, initial=Devices.States[7], ignore_invalid_triggers=True)

        # States.idle
        # -> States.start
        # -> States.stop
        self._machine.on_enter_idle('_enter_idle')
        self._machine.on_exit_idle('_exit_idle')
        self._machine.add_transition('internal', source='idle', dest=None, after='_idle_tick')
        self._machine.add_transition(trigger='startAutoStep', source='idle', dest='start')

        # States.start
        # -> States.control
        # -> States.temptUp
        # -> States.temptDown
        self._machine.on_enter_start('_enter_start')
        self._machine.on_exit_start('_exit_start')
        self._machine.add_transition('internal', source='start', dest=None, after='_start_tick')
        self._machine.add_transition(trigger='startControl', source='start', dest='control')
        self._machine.add_transition(trigger='nextTemptPoint', source='start', dest='temptDown',
                                     conditions='_next_point_down')
        self._machine.add_transition(trigger='nextTemptPoint', source='start', dest='temptUp')

        # States.temptUp
        # -> States.control
        self._machine.on_enter_temptUp('_enter_temptUp')
        self._machine.on_exit_temptUp('_exit_temptUp')
        self._machine.add_transition('internal', source='temptUp', dest=None, after='_temptUp_tick')
        self._machine.add_transition(trigger='startControl', source='temptUp', dest='control')

        # States.temptDown
        # -> States.control
        self._machine.on_enter_temptDown('_enter_temptDown')
        self._machine.on_exit_temptDown('_exit_temptDown')
        self._machine.add_transition('internal', source='temptDown', dest=None, after='_temptDown_tick')
        self._machine.add_transition(trigger='startControl', source='temptDown', dest='control')

        # States.control
        # -> States.stable
        self._machine.on_enter_control('_enter_control')
        self._machine.on_exit_control('_exit_control')
        self._machine.add_transition('internal', source='control', dest=None, after='_control_tick')
        self._machine.add_transition(trigger='achieveSteady', source='control', dest='stable')

        # States.stable
        # -> States.measure
        self._machine.on_enter_stable('_enter_stable')
        self._machine.on_exit_stable('_exit_stable')
        self._machine.add_transition('internal', source='stable', dest=None, after='_stable_tick')
        self._machine.add_transition(trigger='startMeasure', source='stable', dest='measure')

        # States.measure
        # -> States.temptUp
        # -> States.temptDown
        self._machine.on_enter_measure('_enter_measure')
        self._machine.on_exit_measure('_exit_measure')
        self._machine.add_transition('internal', source='measure', dest=None, after='_measure_tick')
        self._machine.add_transition(trigger='nextTemptPoint', source='measure', dest='temptDown',
                                     conditions='_next_point_down')
        self._machine.add_transition(trigger='nextTemptPoint', source='measure', dest='temptUp')
        self._machine.add_transition(trigger='finishAll', source='measure', dest='stop',
                                     conditions='_stop_when_finished')
        self._machine.add_transition(trigger='finishAll', source='measure', dest='idle')

        # States.stop
        self._machine.on_enter_stop('_enter_stop')
        self._machine.on_exit_stop('_exit_stop')
        self._machine.add_transition('internal', source='stop', dest=None, after='_stop_tick')

        # suspend the auto control
        self._machine.add_transition(trigger='suspendAutoControl',
                                     source=['start', 'temptUp', 'temptDown', 'control', 'stable', 'measure'],
                                     dest='idle')

        # force to stop
        self._machine.add_transition(trigger='forceStop', source='*', dest='stop')

    def start_timer(self):
        self._timer.start()

    # States idle
    def _enter_idle(self):
        print('enter the idle state')
        # clear state time count
        self.currentTemptPointState.stateCount = 0
        # state change signal
        self.controlStateChangedSignal.emit(['idle'])

    def _exit_idle(self):
        print('exit the idle state')
        pass

    def _idle_tick(self, sec):
        print('idle tick')
        # if start auto control as well as there tpPoint in the list
        if self.autoControl is True and len(self.temptPointList) != 0:
            self._machine.startAutoStep()
        pass

    # States start
    def _enter_start(self):
        print('enter the start state')
        # clear state time count
        self.currentTemptPointState.stateCount = 0
        # state change signal
        self.controlStateChangedSignal.emit(['start'])

    def _exit_start(self):
        print('exit the start state')
        pass

    @typeassert(sec=float)
    def _start_tick(self, sec):
        print('start tick')
        for pt in self.temptPointList:
            if pt.finished == False:
                self.currentTemptPointState = pt
        # if all the points have been measured
        # which means the finished of all the point is True
        # then suspend the auto control and go to idle
        if self.currentTemptPointState.finished == True:
            self._machine.suspendAutoControl()
            return

        # else start the auto control flow
        if abs(self.currentTemptPointState.stateTemp - self.tpDevice.temperatures[-1]) < self.thrParam.controlTemptThr:
            self._machine.startControl()
        else:
            self._machine.nextTemptPoint()

    def _next_point_down(self):
        if self.currentTemptPointState.stateTemp() < self.tpDevice.temperatures[-1]:
            return True
        else:
            return False

    # States temptUp
    def _enter_temptUp(self):
        print('enter tempUp')
        # update relay status
        rySt = [False] * 16
        rySt[RelayProtocol.CmdRelay.Elect] = True
        rySt[RelayProtocol.CmdRelay.MainHeat] = True
        rySt[RelayProtocol.CmdRelay.Cool] = False
        rySt[RelayProtocol.CmdRelay.Circle] = True
        errR, st = self.ryDevice.updatestatustodevice(rySt, True)
        self.ryStatusUpdateSignal.emit([errR, st])
        # update T-C parameters
        errT = self.tpDevice.updateparamtodevice(self.currentTemptPointState.paramM, True)
        self.tpParamUpdateSignal.emit(errT, self.currentTemptPointState.paramM)
        # clear state time count
        self.currentTemptPointState.stateCount = 0
        # state change signal
        self.controlStateChangedSignal.emit(['temptUp'])

    def _exit_temptUp(self):
        print('exit the temptUp state')
        pass

    @typeassert(sec=float)
    def _temptUp_tick(self, sec):
        print('temptUp tick: %d' % sec)
        # error check

        # judge enter control
        if self.tpDevice.temperatures[-1] > self.currentTemptPointState.stateTemp() - 0.1:
            self._machine.startControl()

    # States temptDown
    def _enter_temptDown(self):
        print('enter the temptDown state')
        # update relay status
        rySt = [False] * 16
        rySt[RelayProtocol.CmdRelay.Elect] = True
        rySt[RelayProtocol.CmdRelay.MainHeat] = False
        rySt[RelayProtocol.CmdRelay.Cool] = True
        rySt[RelayProtocol.CmdRelay.Circle] = True
        errR, st = self.ryDevice.updatestatustodevice(rySt, True)
        self.ryStatusUpdateSignal.emit([errR, st])
        # update T-C parameters
        errT = self.tpDevice.updateparamtodevice(self.currentTemptPointState.paramM, True)
        self.tpParamUpdateSignal.emit(errT, self.currentTemptPointState.paramM)
        # clear state time count
        self.currentTemptPointState.stateCount = 0
        # state change signal
        self.controlStateChangedSignal.emit(['temptDown'])

    def _exit_temptDown(self):
        print('exit the temptDown state')
        pass

    @typeassert(sec=float)
    def _temptDown_tick(self, sec):
        print('temptDown tick: %d' % sec)
        # error check

        # judge enter control
        if self.tpDevice.temperatures[-1] < self.currentTemptPointState.stateTemp() + 0.1:
            self._machine.startControl()

    # States control
    def _enter_control(self):
        print('enter the control state')
        rySt = [False] * 16
        rySt[RelayProtocol.CmdRelay.Elect] = True
        rySt[RelayProtocol.CmdRelay.MainHeat] = False
        rySt[RelayProtocol.CmdRelay.Cool] = True
        rySt[RelayProtocol.CmdRelay.Circle] = True
        errR, st = self.ryDevice.updatestatustodevice(rySt, True)
        self.ryStatusUpdateSignal.emit([errR, st])
        # clear state time count
        self.currentTemptPointState.stateCount = 0
        # state change signal
        self.controlStateChangedSignal.emit(['control'])

    def _exit_control(self):
        print('exit the control state')
        pass

    @typeassert(sec=float)
    def _control_tick(self, sec):
        print('control tick: %d' % sec)
        # error check

        # if the fluctuation satisfy the criteria, then go to stable
        if self.tpDevice.check_fluc_cnt(self.thrParam.steadyTimeSec/self.thrParam.tpUpdateInterval,
                                        self.thrParam.flucValue):
            self._machine.achieveSteady()

    # States stable
    def _enter_stable(self):
        print('enter the stable state')
        rySt = [False] * 16
        rySt[RelayProtocol.CmdRelay.Elect] = True
        rySt[RelayProtocol.CmdRelay.MainHeat] = False
        rySt[RelayProtocol.CmdRelay.Cool] = True
        rySt[RelayProtocol.CmdRelay.Circle] = True
        errR, st = self.ryDevice.updatestatustodevice(rySt, True)
        self.ryStatusUpdateSignal.emit([errR, st])
        # clear state time count
        self.currentTemptPointState.stateCount = 0
        # state change signal
        self.controlStateChangedSignal.emit(['stable'])

    def _exit_stable(self):
        print('exit the stable state')
        pass

    @typeassert(sec=float)
    def _stable_tick(self, sec):
        print('stable tick: %d' % sec)
        # enter this state more than xx time
        # then check the fluctuation again
        if self.currentTemptPointState.stateCount > \
                self.thrParam.bridgeSteadyTimeSec/self.thrParam.tpUpdateInterval and\
                self.tpDevice.check_fluc_cnt(self.thrParam.steadyTimeSec /
                                             self.thrParam.tpUpdateInterval,self.thrParam.flucValue):
            self._machine.startMeasure()

    # States measure
    def _enter_measure(self):
        print('enter the measure state')
        # clear state time count
        self.currentTemptPointState.stateCount = 0
        # state change signal
        self.controlStateChangedSignal.emit(['measure'])

    def _exit_measure(self):
        print('exit the measure state')
        pass

    @typeassert(sec=float)
    def _measure_tick(self, sec):
        print('measure tick: %d' % sec)
        # error check

        #
        self.temptPointList[self.currentTemptPointState.temptPointIndex].finished = True
        # search in the list, and find whether there is still any point which is unfinished
        for pt in self.temptPointList:
            if pt.finished == False:
                self.currentTemptPointState = pt

        # all the point is finished
        if self.currentTemptPointState.finished == True:
            self._machine.finishAll()
        else:
            self._machine.nextTemptPoint()

    def _stop_when_finished(self):
        return self.thrParam.shutDownComputer

    # States stop
    def _enter_stop(self):
        print('enter the stop state')
        # clear state time count
        self.currentTemptPointState.stateCount = 0
        # state change signal
        self.controlStateChangedSignal.emit(['stop'])

    def _exit_stop(self):
        print('exit the stop state')
        pass

    @typeassert(sec=float)
    def _stop_tick(self, sec):
        print('stop tick: %d' % sec)
        pass

    @typeassert(sec=float)
    def _timer_tick(self, sec):
        """
        device timer tick function
        :param tm: timer interval
        :return:
        """
        # read temperature and power value
        errT, valT = self.tpDevice.gettempshow(True)
        errP, valP = self.tpDevice.getpowershow(True)
        self.tpUpdateTickSignal.emit([errT, valT, errP, valP])
        # state count
        # bug : wghou 20190213 overflow
        self.currentTemptPointState.stateCount += 1
        # state transition
        if __debug__:
            self._machine.internal(sec)
            #
            self._timer = threading.Timer(self.thrParam.tpUpdateInterval, self._timer_tick, [self.thrParam.tpUpdateInterval])
            self._timer.start()
        else:
            self._timer = threading.Timer(self.thrParam.tpUpdateInterval, self._timer_tick, [self.thrParam.tpUpdateInterval])
            self._timer.start()
            #
            self._machine.internal(sec * 1000)


if __name__ == '__main__':
    model = Devices('test')
    model.internal(2000)

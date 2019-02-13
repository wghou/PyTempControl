# -*- coding: utf-8 -*-


import threading
import time
from enum import Enum, unique
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

    def __init__(self, name):
        # tempt parameters
        # relay device
        self.ryDevice = RelayDevice()
        # temperature control device
        self.tpDevice = TemptDevice()
        # temperature list
        self.temptPointList = None
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

    @typeassert(cmd=RelayProtocol.CmdRelay, st=bool)
    def set_rystatus(self, cmd, st):
        from Device.RelayDevice import RelayComThread
        self.ryDevice.ryStatusToSet[cmd] = st
        ryThread = RelayComThread(self.ryDevice)
        ryThread.finishSignal.connect(self.set_rystatus_end)
        ryThread.start()

    def set_rystatus_end(self, err):
        print(err)



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

        # States.stop
        self._machine.on_enter_stop('_enter_stop')
        self._machine.on_exit_stop('_exit_stop')
        self._machine.add_transition('internal', source='stop', dest=None, after='_stop_tick')

        # suspend the auto control
        self._machine.add_transition(trigger='suspendAutoControl',
                                     source=['temptUp', 'temptDown', 'control', 'stable', 'measure'],
                                     dest='idle')

        # force to stop
        self._machine.add_transition(trigger='forceStop', source='*', dest='stop')

    ###
    # States idle
    def _enter_idle(self):
        print('enter the idle state')
        pass

    def _exit_idle(self):
        print('exit the idle state')
        pass

    def _idle_tick(self, mSec):
        print('idle tick: %d' %mSec)
        pass

    ###
    # States start
    def _enter_start(self):
        print('enter the start state')
        pass

    def _exit_start(self):
        print('exit the start state')
        pass

    def _start_tick(self, mSec):
        print('start tick: %d' %mSec)
        pass

    def _next_point_down(self):
        return True

    ###
    # States temptUp
    def _enter_temptUp(self):
        print('enter the temptUp state')
        pass

    def _exit_temptUp(self):
        print('exit the temptUp state')
        pass

    def _temptUp_tick(self, mSec):
        print('temptUp tick: %d' % mSec)
        pass


    ###
    # States temptDown
    def _enter_temptDown(self):
        print('enter the temptDown state')
        pass

    def _exit_temptDown(self):
        print('exit the temptDown state')
        pass

    def _temptDown_tick(self, mSec):
        print('temptDown tick: %d' % mSec)
        pass

    ###
    # States control
    def _enter_control(self):
        print('enter the control state')
        pass

    def _exit_control(self):
        print('exit the control state')
        pass

    def _control_tick(self, mSec):
        print('control tick: %d' % mSec)
        pass

    ###
    # States stable
    def _enter_stable(self):
        print('enter the stable state')
        pass

    def _exit_stable(self):
        print('exit the stable state')
        pass

    def _stable_tick(self, mSec):
        print('stable tick: %d' % mSec)
        pass

    ###
    # States measure
    def _enter_measure(self):
        print('enter the measure state')
        pass

    def _exit_measure(self):
        print('exit the measure state')
        pass

    def _measure_tick(self, mSec):
        print('measure tick: %d' % mSec)
        pass

    ###
    # States stop
    def _enter_stop(self):
        print('enter the stop state')
        pass

    def _exit_stop(self):
        print('exit the stop state')
        pass

    def _stop_tick(self, mSec):
        print('stop tick: %d' % mSec)
        pass


if __name__ == '__main__':
    model = Devices('test')
    model.internal(2000)
    model.startAutoStep()
    model.internal(2000)
    model.nextTemptPoint()
    model.internal(2000)
    model.startControl()

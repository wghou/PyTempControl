# -*- coding: utf-8 -*-



from enum import IntEnum



class StatesEnum(IntEnum):
    start = 0
    temptUp = 1
    temptDown = 2
    control = 3
    stable = 4
    measure = 5
    stop = 6
    idle = 7
    undefined = 8


class TemptPointStruct(object):
    def __init__(self):
        # the position of this tpPoint in the list
        self.temptPointIndex = 0
        # whether finished of this tpPoint
        self.finished = True
        # the parameters of T-C board in this tpPoint
        self.paramM = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        # the flow state
        self._state = StatesEnum.idle
        # the time count
        self.stateCount = 0

    def stateTemp(self):
        """
        the target temperature of this tpPoint
        :return: return the target temperature
        """
        return self.paramM[0]


class ThresholdParamStruct(object):
    def __init__(self):
        self.ryElectEnable = False
        self.steadyTimeSec = 300
        self.bridgeSteadyTimeSec = 120
        self.flucValue = 0.001
        self.controlTemptThr = 0.4
        self.temptNoUpOrDownFaultTimeSec = 600
        self.temptNotUpOrDownFaultThr = 0.4
        self.flucFaultTimeSec = 120
        self.flucFaultThr = 0.4
        self.tempBiasFaultThr = 2.0
        self.temptMaxValue = 40.0
        self.temptMinValue = -2.0
        self.sort = 'descend'
        self.shutDownComputer = False
        self.tpUpdateInterval = 4.0
        #
        self.sunCoolAndCircleShutdownThr = 36.0
        self.temptDownCoolFShoutDownDevision = 12.5
        self.tempDownCoolFShoutDownHot = 0.4
        self.temptDownCoolFShoutDownCool = 0.2

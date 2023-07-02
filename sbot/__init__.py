from .arduino import AnalogPins, GPIOPinMode
from .exceptions import (
    BoardDisconnectionError, MetadataKeyError, MetadataNotReadyError,
)
from .game_specific import GAME_LENGTH
from .logging import add_trace_level
from .motor_board import MotorPower
from .power_board import Note, PowerOutputPosition
from .robot import Robot

add_trace_level()

A0 = AnalogPins.A0
A1 = AnalogPins.A1
A2 = AnalogPins.A2
A3 = AnalogPins.A3
A4 = AnalogPins.A4
A5 = AnalogPins.A5

H0 = PowerOutputPosition.H0
H1 = PowerOutputPosition.H1
L0 = PowerOutputPosition.L0
L1 = PowerOutputPosition.L1
L2 = PowerOutputPosition.L2
L3 = PowerOutputPosition.L3

BRAKE = MotorPower.BRAKE
COAST = MotorPower.COAST

__all__ = [
    'A0',
    'A1',
    'A2',
    'A3',
    'A4',
    'A5',
    'BoardDisconnectionError',
    'BRAKE',
    'COAST',
    'GAME_LENGTH',
    'GPIOPinMode',
    'H0',
    'H1',
    'L0',
    'L1',
    'L2',
    'L3',
    'MetadataKeyError',
    'MetadataNotReadyError',
    'Note',
    'Robot',
]

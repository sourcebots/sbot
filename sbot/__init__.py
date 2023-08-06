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

BRAKE = MotorPower.BRAKE
COAST = MotorPower.COAST

__all__ = [
    'AnalogPins',
    'BoardDisconnectionError',
    'BRAKE',
    'COAST',
    'GAME_LENGTH',
    'GPIOPinMode',
    'MetadataKeyError',
    'MetadataNotReadyError',
    'Note',
    'PowerOutputPosition',
    'Robot',
]

from ..game_specific import GAME_LENGTH
from ..internal.exceptions import (
    BoardDisconnectionError,
    MetadataKeyError,
    MetadataNotReadyError,
)
from ..internal.logging import add_trace_level
from .arduino import AnalogPins, GPIOPinMode
from .leds import Colour
from .motor_board import MotorPower
from .power_board import Note, PowerOutputPosition
from .robot import Robot

add_trace_level()

BRAKE = MotorPower.BRAKE
COAST = MotorPower.COAST

__all__ = [
    'BRAKE',
    'COAST',
    'GAME_LENGTH',
    'AnalogPins',
    'BoardDisconnectionError',
    'Colour',
    'GPIOPinMode',
    'MetadataKeyError',
    'MetadataNotReadyError',
    'Note',
    'PowerOutputPosition',
    'Robot',
]

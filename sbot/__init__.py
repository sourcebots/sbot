"""SourceBots API."""

from j5.boards.sb.arduino import AnaloguePin
from j5.boards.sr.v4.power_board import PowerOutputPosition
from j5.components.gpio_pin import GPIOPinMode
from j5.components.motor import MotorSpecialState
from j5.components.piezo import Note

from .logging import logger_setup
from .robot import Robot, __version__

logger_setup()

COAST = MotorSpecialState.COAST
BRAKE = MotorSpecialState.BRAKE

__all__ = [
    "__version__",
    "AnaloguePin",
    "BRAKE",
    "COAST",
    "GPIOPinMode",
    "Note",
    "PowerOutputPosition",
    "Robot",
]

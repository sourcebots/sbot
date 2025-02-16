from os import environ as _environ

from .arduinos import AnalogPin, GPIOPinMode
from .leds import Colour
from .motors import MotorPower
from .power import PowerOutputPosition
from .utils import Note

if 'SBOT_PYTEST' not in _environ:
    from .robot import arduino, comp, leds, motors, power, servos, utils, vision

BRAKE = MotorPower.BRAKE
COAST = MotorPower.COAST

__all__ = [
    'BRAKE',
    'COAST',
    'AnalogPin',
    'Colour',
    'GPIOPinMode',
    'MotorPower',
    'Note',
    'PowerOutputPosition',
    'arduino',
    'comp',
    'leds',
    'motors',
    'power',
    'servos',
    'utils',
    'vision',
]

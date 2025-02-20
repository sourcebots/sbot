from os import environ as _environ

from ._arduinos import AnalogPin, GPIOPinMode
from ._leds import Colour
from ._motors import MotorPower
from ._power import PowerOutputPosition
from ._utils import Note

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

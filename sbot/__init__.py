"""SourceBots API."""

from j5.components.motor import MotorSpecialState

from .logging import logger_setup
from .robot import Robot, __version__

logger_setup()

COAST = MotorSpecialState.COAST
BRAKE = MotorSpecialState.BRAKE

__all__ = [
    "__version__",
    "BRAKE",
    "COAST",
    "Robot",
]

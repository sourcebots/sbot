"""Environment definitions."""
from typing import Type, cast

from j5.backends import Backend, Environment
from j5.backends.console.sb.arduino import SBArduinoConsoleBackend
from j5.backends.console.sr.v4 import (
    SRV4MotorBoardConsoleBackend,
    SRV4PowerBoardConsoleBackend,
)
from j5.backends.console.sr.v4.servo_board import SRV4ServoBoardConsoleBackend
from j5.backends.hardware.sb.arduino import SBArduinoHardwareBackend
from j5.backends.hardware.sr.v4 import (
    SRV4MotorBoardHardwareBackend,
    SRV4PowerBoardHardwareBackend,
    SRV4ServoBoardHardwareBackend,
)

from sbot.vision.backend import SBZolotoSingleHardwareBackend

__all__ = [
    "HardwareEnvironment",
]

HardwareEnvironment = Environment("Hardware Environment")

HardwareEnvironment.register_backend(SRV4PowerBoardHardwareBackend)
HardwareEnvironment.register_backend(SRV4ServoBoardHardwareBackend)
HardwareEnvironment.register_backend(SRV4MotorBoardHardwareBackend)
HardwareEnvironment.register_backend(SBArduinoHardwareBackend)
HardwareEnvironment.register_backend(SBZolotoSingleHardwareBackend)

ConsoleEnvironment = Environment("Console Environment")

ConsoleEnvironment.register_backend(SRV4PowerBoardConsoleBackend)
ConsoleEnvironment.register_backend(SRV4ServoBoardConsoleBackend)
ConsoleEnvironment.register_backend(SRV4MotorBoardConsoleBackend)
ConsoleEnvironment.register_backend(SBArduinoConsoleBackend)

CONSOLE_ENVIRONMENT_WITH_VISION = Environment("Console Environment with Vision")

CONSOLE_ENVIRONMENT_WITH_VISION.register_backend(SRV4PowerBoardConsoleBackend)
CONSOLE_ENVIRONMENT_WITH_VISION.register_backend(SRV4ServoBoardConsoleBackend)
CONSOLE_ENVIRONMENT_WITH_VISION.register_backend(SRV4MotorBoardConsoleBackend)
CONSOLE_ENVIRONMENT_WITH_VISION.register_backend(SBArduinoConsoleBackend)
CONSOLE_ENVIRONMENT_WITH_VISION.register_backend(SBZolotoSingleHardwareBackend)

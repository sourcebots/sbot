"""Environment definitions."""
from typing import Type, cast

from j5.backends import Backend, Environment
from j5.backends.hardware.sb.arduino import SBArduinoHardwareBackend
from j5.backends.hardware.sr.v4 import (
    SRV4MotorBoardHardwareBackend,
    SRV4PowerBoardHardwareBackend,
    SRV4ServoBoardHardwareBackend,
)

HardwareEnvironment = Environment("Hardware Environment")

HardwareEnvironment.register_backend(cast(Type[Backend], SRV4PowerBoardHardwareBackend))
HardwareEnvironment.register_backend(cast(Type[Backend], SRV4ServoBoardHardwareBackend))
HardwareEnvironment.register_backend(cast(Type[Backend], SRV4MotorBoardHardwareBackend))
HardwareEnvironment.register_backend(cast(Type[Backend], SBArduinoHardwareBackend))

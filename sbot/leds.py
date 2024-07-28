"""User LED Driver."""
from __future__ import annotations

import atexit
import warnings
from enum import IntEnum, unique
from types import MappingProxyType
from typing import Literal, Mapping, NamedTuple, Optional

from .utils import IN_SIMULATOR

try:
    import RPi.GPIO as GPIO  # isort: ignore
    HAS_HAT = True if not IN_SIMULATOR else False
except ImportError:
    HAS_HAT = False


class RGBled(NamedTuple):
    """RGB LED."""
    red: int
    green: int
    blue: int


@unique
class RobotLEDs(IntEnum):
    """Mapping of LEDs to GPIO Pins."""

    START = 9

    USER_A_RED = 24
    USER_A_GREEN = 10
    USER_A_BLUE = 25
    USER_B_RED = 27
    USER_B_GREEN = 23
    USER_B_BLUE = 22
    USER_C_RED = 4
    USER_C_GREEN = 18
    USER_C_BLUE = 17

    @classmethod
    def all_user_leds(cls) -> list[int]:
        """Get all LEDs."""
        return [c.value for c in cls if c.name != 'START']

    @classmethod
    def user_leds(cls) -> dict[Literal['A', 'B', 'C'], RGBled]:
        """Get the user programmable LEDs."""
        return {
            'A': RGBled(cls.USER_A_RED, cls.USER_A_GREEN, cls.USER_A_BLUE),
            'B': RGBled(cls.USER_B_RED, cls.USER_B_GREEN, cls.USER_B_BLUE),
            'C': RGBled(cls.USER_C_RED, cls.USER_C_GREEN, cls.USER_C_BLUE),
        }


class Colour():
    """User LED colours."""

    OFF = (False, False, False)
    RED = (True, False, False)
    YELLOW = (True, True, False)
    GREEN = (False, True, False)
    CYAN = (False, True, True)
    BLUE = (False, False, True)
    MAGENTA = (True, False, True)
    WHITE = (True, True, True)


def get_user_leds() -> Mapping[Literal['A', 'B', 'C'], LED]:
    """Get the user programmable LEDs."""
    if HAS_HAT:
        GPIO.setmode(GPIO.BCM)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

            # If this is not the first time the code is run this init will
            # cause a warning as the gpio are already initialized, we can
            # suppress this as we know the reason behind the warning
            GPIO.setup(RobotLEDs.all_user_leds(), GPIO.OUT, initial=GPIO.LOW)
        return MappingProxyType({
            k: PhysicalLED(v) for k, v in RobotLEDs.user_leds().items()
        })
    elif IN_SIMULATOR:
        return MappingProxyType({
            k: SimulationLED(v) for k, v in RobotLEDs.user_leds().items()
        })
    else:
        return MappingProxyType({
            k: LED(v) for k, v in RobotLEDs.user_leds().items()
        })


class StartLed:
    """
    Start LED.

    This is an internal class and should only be used by the Robot class.
    """
    __slots__ = ('_pwm',)

    def __init__(self) -> None:
        if HAS_HAT:
            self._pwm: Optional[GPIO.PWM] = None
            GPIO.setmode(GPIO.BCM)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")

                # If this is not the first time the code is run this init will
                # cause a warning as the gpio are already initialized, we can
                # suppress this as we know the reason behind the warning
                GPIO.setup(RobotLEDs.START, GPIO.OUT, initial=GPIO.LOW)

            # Cleanup just the start LED to turn it off when the code exits
            # Mypy isn't aware of the version of atexit.register(func, *args)
            atexit.register(GPIO.cleanup, RobotLEDs.START)  # type: ignore[call-arg]

    def set_state(self, state: bool) -> None:
        """Set the start LED to on or off."""
        if HAS_HAT:
            if self._pwm:
                # stop any flashing the LED is doing
                self._pwm.stop()
                self._pwm = None
            GPIO.output(RobotLEDs.START, GPIO.HIGH if state else GPIO.LOW)

    def flash_start(self) -> None:
        """Enable flashing the start LED."""
        if HAS_HAT:
            self._pwm = GPIO.PWM(RobotLEDs.START, 1)
            self._pwm.start(50)

    def get_state(self) -> bool:
        """Get the state of the start LED."""
        return GPIO.input(RobotLEDs.START) if HAS_HAT else False


class LED:
    """
    User programmable LED.

    This is a dummy class to handle the case where this is run on neither the
    Raspberry Pi nor the simulator.
    As such, this class does nothing.
    """
    __slots__ = ('_led',)

    def __init__(self, led: RGBled) -> None:
        self._led = led

    @property
    def colour(self) -> tuple[bool, bool, bool]:
        """Get the colour of the user LED."""
        return False, False, False

    @colour.setter
    def colour(self, value: tuple[bool, bool, bool]) -> None:
        """Set the colour of the user LED."""
        if not isinstance(value, (tuple, list)) or len(value) != 3:
            raise ValueError("The LED requires 3 values for its colour")


class PhysicalLED(LED):
    """
    User programmable LED.

    Used when running on the Raspberry Pi to control the actual LEDs.
    """
    __slots__ = ('_led',)

    def __init__(self, led: RGBled) -> None:
        self._led = led

    @property
    def colour(self) -> tuple[bool, bool, bool]:
        """Get the colour of the user LED."""
        return (
            GPIO.input(self._led.red),
            GPIO.input(self._led.green),
            GPIO.input(self._led.blue),
        )

    @colour.setter
    def colour(self, value: tuple[bool, bool, bool]) -> None:
        """Set the colour of the user LED."""
        if not isinstance(value, (tuple, list)) or len(value) != 3:
            raise ValueError("The LED requires 3 values for its colour")

        GPIO.output(
            self._led,
            tuple(
                GPIO.HIGH if v else GPIO.LOW for v in value
            ),
        )


class SimulationLED(LED):
    """
    User programmable LED.

    Used when running in the simulator to control the simulated LEDs.
    """
    __slots__ = ('_led',)

    def __init__(self, led: RGBled) -> None:
        self._led = led

    @property
    def colour(self) -> tuple[bool, bool, bool]:
        """Get the colour of the user LED."""
        return False, False, False

    @colour.setter
    def colour(self, value: tuple[bool, bool, bool]) -> None:
        """Set the colour of the user LED."""
        if not isinstance(value, (tuple, list)) or len(value) != 3:
            raise ValueError("The LED requires 3 values for its colour")

        pass

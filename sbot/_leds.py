"""User LED Driver."""
from __future__ import annotations

import warnings
from enum import Enum, IntEnum, unique
from typing import NamedTuple

from .internal.board_manager import BoardManager, DiscoveryTemplate
from .internal.utils import IN_SIMULATOR

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
    def user_leds(cls) -> list[RGBled]:
        """Get the user programmable LEDs."""
        return [
            RGBled(cls.USER_A_RED, cls.USER_A_GREEN, cls.USER_A_BLUE),
            RGBled(cls.USER_B_RED, cls.USER_B_GREEN, cls.USER_B_BLUE),
            RGBled(cls.USER_C_RED, cls.USER_C_GREEN, cls.USER_C_BLUE),
        ]


class Colour(Enum):
    """User LED colours."""

    OFF = (False, False, False)
    RED = (True, False, False)
    YELLOW = (True, True, False)
    GREEN = (False, True, False)
    CYAN = (False, True, True)
    BLUE = (False, False, True)
    MAGENTA = (True, False, True)
    WHITE = (True, True, True)


class Led:
    """User LED Driver."""

    def __init__(self, boards: BoardManager):
        # Register led proxy
        template = DiscoveryTemplate(
            identifier='led',
            name='led server',
            vid=0,  # Unused
            pid=0,  # Unused
            board_type='KCHv1B',
            sim_only=True,
            sim_board_type='LedBoard',
            max_boards=1,
        )
        BoardManager.register_board(template)
        self._boards = boards

        if HAS_HAT:
            GPIO.setmode(GPIO.BCM)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")

                # If this is not the first time the code is run this init will
                # cause a warning as the gpio are already initialized, we can
                # suppress this as we know the reason behind the warning
                GPIO.setup(RobotLEDs.all_user_leds(), GPIO.OUT, initial=GPIO.LOW)

    def set_colour(self, id: int, colour: Colour) -> None:
        """
        Set the colour of the user LED.

        :param id: The ID of the user LED.
        :param colour: The colour to set the LED to.
        """
        self._validate_id(id)
        red = colour.value[0]
        green = colour.value[1]
        blue = colour.value[2]

        if IN_SIMULATOR:
            led_proxy = self._boards.get_first_board('led')
            led_proxy.write(f'LED:{id}:SET:{red:d}:{green:d}:{blue:d}')
        elif HAS_HAT:
            GPIO.output(RobotLEDs.user_leds()[id], colour.value)

    def get_colour(self, id: int) -> Colour:
        """
        Get the colour of the user LED.

        :param id: The ID of the user LED.
        :return: The colour of the LED.
        """
        self._validate_id(id)
        if IN_SIMULATOR:
            led_proxy = self._boards.get_first_board('led')
            response = led_proxy.query(f'LED:{id}:GET?')
            red, green, blue = response.split(':')
            return Colour(
                # Convert string to bool
                (red != '0', green != '0', blue != '0')
            )
        elif HAS_HAT:
            led = RobotLEDs.user_leds()[id]
            Colour((
                GPIO.input(led.red),
                GPIO.input(led.green),
                GPIO.input(led.blue),
            ))
            return Colour.OFF
        else:
            return Colour.OFF

    def _validate_id(self, id: int) -> None:
        if id not in range(3):
            raise ValueError(f'Invalid LED ID: {id}')

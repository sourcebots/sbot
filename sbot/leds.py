"""User LED Driver."""
from __future__ import annotations

import atexit
import logging
import warnings
from enum import Enum, IntEnum, unique
from types import MappingProxyType
from typing import Literal, Mapping, NamedTuple, Optional

from .exceptions import BoardDisconnectionError, IncorrectBoardError
from .serial_wrapper import SerialWrapper
from .utils import IN_SIMULATOR, Board, BoardIdentity, get_simulator_boards

try:
    import RPi.GPIO as GPIO  # isort: ignore
    HAS_HAT = True if not IN_SIMULATOR else False
except ImportError:
    HAS_HAT = False


logger = logging.getLogger(__name__)

# Only used in the simulator
BAUDRATE = 115200


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
        led_server = LedServer.initialise()
        if led_server is not None:
            return MappingProxyType({
                k: SimulationLED(v, led_server)
                for v, k in enumerate(RobotLEDs.user_leds().keys())
            })
        else:
            return MappingProxyType({
                k: LED(v) for k, v in RobotLEDs.user_leds().items()
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
    def colour(self) -> Colour:
        """Get the colour of the user LED."""
        return Colour.OFF

    @colour.setter
    def colour(self, value: Colour) -> None:
        """Set the colour of the user LED."""
        pass


class PhysicalLED(LED):
    """
    User programmable LED.

    Used when running on the Raspberry Pi to control the actual LEDs.
    """
    __slots__ = ('_led',)

    def __init__(self, led: RGBled) -> None:
        self._led = led

    @property
    def colour(self) -> Colour:
        """Get the colour of the user LED."""
        return Colour((
            GPIO.input(self._led.red),
            GPIO.input(self._led.green),
            GPIO.input(self._led.blue),
        ))

    @colour.setter
    def colour(self, value: Colour) -> None:
        """Set the colour of the user LED."""
        GPIO.output(
            self._led,
            tuple(
                GPIO.HIGH if v else GPIO.LOW for v in value.value
            ),
        )


class LedServer(Board):
    """
    LED control over a socket.

    Used when running in the simulator to control the simulated LEDs.
    """

    @staticmethod
    def get_board_type() -> str:
        """
        Return the type of the board.

        :return: The literal string 'KCHv1B'.
        """
        return 'KCHv1B'

    def __init__(
        self,
        serial_port: str,
        initial_identity: BoardIdentity | None = None,
    ) -> None:
        if initial_identity is None:
            initial_identity = BoardIdentity()
        self._serial = SerialWrapper(
            serial_port,
            BAUDRATE,
            identity=initial_identity,
        )

        self._identity = self.identify()
        if self._identity.board_type != self.get_board_type():
            raise IncorrectBoardError(self._identity.board_type, self.get_board_type())
        self._serial.set_identity(self._identity)

        # Reset the board to a known state
        self._serial.write('*RESET')

    @classmethod
    def initialise(cls) -> 'LedServer' | None:
        """Initialise the LED server using simulator discovery."""
        # The filter here is the name of the emulated board in the simulator
        boards = get_simulator_boards('LedBoard')

        if not boards:
            return None

        board_info = boards[0]

        # Create board identity from the info given
        initial_identity = BoardIdentity(
            manufacturer='sbot_simulator',
            board_type=board_info.type_str,
            asset_tag=board_info.serial_number,
        )

        try:
            board = cls(board_info.url, initial_identity)
        except BoardDisconnectionError:
            logger.warning(
                f"Simulator specified LED board at port {board_info.url!r}, "
                "could not be identified. Ignoring this device")
            return None
        except IncorrectBoardError as err:
            logger.warning(
                f"Board returned type {err.returned_type!r}, "
                f"expected {err.expected_type!r}. Ignoring this device")
            return None

        return board

    def identify(self) -> BoardIdentity:
        """
        Get the identity of the board.

        :return: The identity of the board.
        """
        response = self._serial.query('*IDN?')
        return BoardIdentity(*response.split(':'))

    def set_leds(self, led_num: int, value: tuple[bool, bool, bool]) -> None:
        """Set the colour of the LED."""
        self._serial.write(f'LED:{led_num}:SET:{value[0]:d}:{value[1]:d}:{value[2]:d}')

    def get_leds(self, led_num: int) -> tuple[bool, bool, bool]:
        """Get the colour of the LED."""
        response = self._serial.query(f'LED:{led_num}:GET?')
        red, green, blue = response.split(':')
        return bool(int(red)), bool(int(green)), bool(int(blue))


class SimulationLED(LED):
    """
    User programmable LED.

    Used when running in the simulator to control the simulated LEDs.
    """
    __slots__ = ('_led_num', '_server')

    def __init__(self, led_num: int, server: LedServer) -> None:
        self._led_num = led_num
        self._server = server

    @property
    def colour(self) -> Colour:
        """Get the colour of the user LED."""
        return Colour(self._server.get_leds(self._led_num))

    @colour.setter
    def colour(self, value: Colour) -> None:
        """Set the colour of the user LED."""
        self._server.set_leds(
            self._led_num,
            (
                bool(value.value[0]),
                bool(value.value[1]),
                bool(value.value[2]),
            )
        )

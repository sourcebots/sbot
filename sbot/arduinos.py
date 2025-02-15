"""The Arduino module provides an interface to the Arduino firmware."""
from enum import Enum, IntEnum

from .internal.board_manager import BoardManager, DiscoveryTemplate
from .internal.logging import log_to_debug
from .internal.utils import map_to_float


class GPIOPinMode(str, Enum):
    """The possible modes for a GPIO pin."""

    INPUT = 'INPUT'
    INPUT_PULLUP = 'INPUT_PULLUP'
    OUTPUT = 'OUTPUT'


class AnalogPin(IntEnum):
    """The analog pins on the Arduino."""

    A0 = 14
    A1 = 15
    A2 = 16
    A3 = 17
    A4 = 18
    A5 = 19


DISABLED_PINS = (0, 1)
AVAILABLE_PINS = range(0, max(AnalogPin) + 1)

ADC_MAX = 1023  # 10 bit ADC
ADC_MIN = 0

SUPPORTED_VID_PIDS = {
    (0x2341, 0x0043),  # Arduino Uno rev 3
    (0x2A03, 0x0043),  # Arduino Uno rev 3
    (0x1A86, 0x7523),  # Uno
    (0x10C4, 0xEA60),  # Ruggeduino
    (0x16D0, 0x0613),  # Ruggeduino
}


class Arduino:
    """
    The Arduino board interface.

    This is intended to be used with Arduino Uno boards running the sbot firmware.

    :param boards: The BoardManager object containing the arduino board references.
    """

    __slots__ = ('_boards', '_identifier')

    def __init__(self, boards: BoardManager):
        self._identifier = 'arduino'
        template = DiscoveryTemplate(
            identifier=self._identifier,
            name='Arduino',
            vid=0,  # Populated later
            pid=0,
            board_type='Arduino',
            sim_board_type='Arduino',
            use_usb_serial=True,
            delay_after_connect=2,
            max_boards=1,
        )
        # Register all the possible Arduino USB IDs
        for vid, pid in SUPPORTED_VID_PIDS:
            BoardManager.register_board(template._replace(vid=vid, pid=pid))

        self._boards = boards

    @log_to_debug
    def set_pin_mode(self, pin: int, mode: GPIOPinMode) -> None:
        """
        Set the mode of the pin.

        To do analog or digital reads set the mode to INPUT or INPUT_PULLUP.
        To do digital writes set the mode to OUTPUT.

        :param pin: The pin to set the mode of.
        :param value: The mode to set the pin to.
        :raises IOError: If the pin mode is not a GPIOPinMode.
        :raises IOError: If this pin cannot be controlled.
        """
        port = self._boards.get_first_board(self._identifier)
        self._validate_pin(pin)
        if not isinstance(mode, GPIOPinMode):
            raise IOError('Pin mode only supports being set to a GPIOPinMode')
        port.write(f'PIN:{pin}:MODE:SET:{mode.value}')

    @log_to_debug
    def digital_read(self, pin: int) -> bool:
        """
        Perform a digital read on the pin.

        :param pin: The pin to read from.
        :raises IOError: If the pin's current mode does not support digital read
        :raises IOError: If this pin cannot be controlled.
        :return: The digital value of the pin.
        """
        port = self._boards.get_first_board(self._identifier)
        self._validate_pin(pin)
        response = port.query(f'PIN:{pin}:DIGITAL:GET?')
        return (response == '1')

    @log_to_debug
    def digital_write(self, pin: int, value: bool) -> None:
        """
        Write a digital value to the pin.

        :param pin: The pin to write to.
        :param value: The value to write to the pin.
        :raises IOError: If the pin's current mode does not support digital write.
        :raises IOError: If this pin cannot be controlled.
        """
        port = self._boards.get_first_board(self._identifier)
        self._validate_pin(pin)
        try:
            if value:
                port.write(f'PIN:{pin}:DIGITAL:SET:1')
            else:
                port.write(f'PIN:{pin}:DIGITAL:SET:0')
        except RuntimeError as e:
            # The firmware returns a NACK if the pin is not in OUTPUT mode
            if 'is not supported in' in str(e):
                raise IOError(str(e))

    @log_to_debug
    def analog_read(self, pin: int) -> float:
        """
        Get the analog voltage on the pin.

        This is returned in volts. Only pins A0-A5 support analog reads.

        :param pin: The pin to read from.
        :raises IOError: If the pin or its current mode does not support analog read.
        :raises IOError: If this pin cannot be controlled.
        :return: The analog voltage on the pin, ranges from 0 to 5.
        """
        port = self._boards.get_first_board(self._identifier)
        self._validate_pin(pin)
        try:
            _ = AnalogPin(pin)
        except ValueError:
            raise IOError('Pin does not support analog read') from None
        try:
            response = port.query(f'PIN:{pin}:ANALOG:GET?')
        except RuntimeError as e:
            # The firmware returns a NACK if the pin is not in INPUT mode
            if 'is not supported in' in str(e):
                raise IOError(str(e))
        # map the response from the ADC range to the voltage range
        return map_to_float(int(response), ADC_MIN, ADC_MAX, 0.0, 5.0)

    @log_to_debug
    def measure_ultrasound_distance(self, pulse_pin: int, echo_pin: int) -> int:
        """
        Measure the distance to an object using an ultrasound sensor.

        The sensor can only measure distances up to 4000mm.

        :param pulse_pin: The pin to send the ultrasound pulse from.
        :param echo_pin: The pin to read the ultrasound echo from.
        :raises ValueError: If either of the pins are invalid
        :return: The distance measured by the ultrasound sensor in mm.
        """
        port = self._boards.get_first_board(self._identifier)
        try:  # bounds check
            self._validate_pin(pulse_pin)
        except (IndexError, IOError):
            raise ValueError("Invalid pulse pin provided") from None
        try:
            self._validate_pin(echo_pin)
        except (IndexError, IOError):
            raise ValueError("Invalid echo pin provided") from None

        response = port.query(f'ULTRASOUND:{pulse_pin}:{echo_pin}:MEASURE?')
        return int(response)

    def _validate_pin(self, pin: int) -> None:
        if pin in DISABLED_PINS:
            raise IOError('This pin cannot be controlled.')
        if pin not in AVAILABLE_PINS:
            raise IndexError(f'Pin {pin} is not available on the Arduino.')

    def __repr__(self) -> str:
        try:
            port = self._boards.get_first_board(self._identifier)
        except (ValueError, KeyError):
            return f"<{self.__class__.__qualname__} no arduino connected>"
        else:
            return f"<{self.__class__.__qualname__} {port}>"

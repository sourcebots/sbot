"""The Arduino module provides an interface to the Arduino firmware."""
from __future__ import annotations

import logging
from enum import Enum, IntEnum
from types import MappingProxyType

from serial.tools.list_ports import comports

from ..internal.exceptions import BoardDisconnectionError, IncorrectBoardError
from ..internal.logging import log_to_debug
from ..internal.serial_wrapper import SerialWrapper
from .utils import (
    IN_SIMULATOR,
    Board,
    BoardIdentity,
    get_simulator_boards,
    get_USB_identity,
    map_to_float,
)

logger = logging.getLogger(__name__)
BAUDRATE = 115200

SUPPORTED_VID_PIDS = {
    (0x2341, 0x0043),  # Arduino Uno rev 3
    (0x2A03, 0x0043),  # Arduino Uno rev 3
    (0x1A86, 0x7523),  # Uno
    (0x10C4, 0xEA60),  # Ruggeduino
    (0x16D0, 0x0613),  # Ruggeduino
}


class GPIOPinMode(str, Enum):
    """The possible modes for a GPIO pin."""

    INPUT = 'INPUT'
    INPUT_PULLUP = 'INPUT_PULLUP'
    OUTPUT = 'OUTPUT'


class AnalogPins(IntEnum):
    """The analog pins on the Arduino."""

    A0 = 14
    A1 = 15
    A2 = 16
    A3 = 17
    A4 = 18
    A5 = 19


class Arduino(Board):
    """
    The Arduino board interface.

    This is intended to be used with Arduino Uno boards running the sbot firmware.

    :param serial_port: The serial port to connect to.
    :param initial_identity: The identity of the board, as reported by the USB descriptor.
    """

    __slots__ = ('_identity', '_pins', '_serial', '_serial_num')

    @staticmethod
    def get_board_type() -> str:
        """
        Return the type of the board.

        :return: The literal string 'Arduino'.
        """
        return 'Arduino'

    def __init__(
        self,
        serial_port: str,
        initial_identity: BoardIdentity | None = None,
    ) -> None:
        if initial_identity is None:
            initial_identity = BoardIdentity()

        # The arduino firmware cannot access the serial number reported in the USB descriptor
        self._serial_num = initial_identity.asset_tag
        self._serial = SerialWrapper(
            serial_port,
            BAUDRATE,
            identity=initial_identity,
            delay_after_connect=2,  # Wait for the board to reset after connecting
        )

        self._pins = (
            tuple(  # Pins 0 and 1 are reserved for serial comms
                Pin(self._serial, index, supports_analog=False, disabled=True)
                for index in range(2))
            + tuple(Pin(self._serial, index, supports_analog=False) for index in range(2, 14))
            + tuple(Pin(self._serial, index, supports_analog=True) for index in range(14, 20))
        )

        self._identity = self.identify()
        if self._identity.board_type != self.get_board_type():
            raise IncorrectBoardError(self._identity.board_type, self.get_board_type())
        self._serial.set_identity(self._identity)

    @classmethod
    def _get_simulator_boards(cls) -> MappingProxyType[str, Arduino]:
        """
        Get the simulator boards.

        :return: A mapping of board serial numbers to Arduinos
        """
        boards = {}
        # The filter here is the name of the emulated board in the simulator
        for board_info in get_simulator_boards('Arduino'):

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
                    f"Simulator specified arduino at port {board_info.url!r}, "
                    "could not be identified. Ignoring this device")
                continue
            except IncorrectBoardError as err:
                logger.warning(
                    f"Board returned type {err.returned_type!r}, "
                    f"expected {err.expected_type!r}. Ignoring this device")
                continue
            boards[board._identity.asset_tag] = board
        return MappingProxyType(boards)

    @classmethod
    def _get_supported_boards(
        cls, manual_boards: list[str] | None = None,
    ) -> MappingProxyType[str, Arduino]:
        """
        Discover the connected Arduinos, by matching the USB descriptor to SUPPORTED_VID_PIDS.

        :param manual_boards: A list of manually specified board port strings,
            defaults to None
        :return: A mapping of board serial numbers to Arduinos
        """
        if IN_SIMULATOR:
            return cls._get_simulator_boards()

        boards = {}
        serial_ports = comports()
        for port in serial_ports:
            if (port.vid, port.pid) in SUPPORTED_VID_PIDS:
                # Create board identity from USB port info
                initial_identity = get_USB_identity(port)

                try:
                    board = Arduino(port.device, initial_identity)
                except BoardDisconnectionError:
                    logger.warning(
                        f"Found Arduino-like serial port at {port.device!r}, "
                        "but it could not be identified. Ignoring this device")
                    continue
                except IncorrectBoardError as err:
                    logger.warning(
                        f"Board returned type {err.returned_type!r}, "
                        f"expected {err.expected_type!r}. Ignoring this device")
                    continue
                boards[board._identity.asset_tag] = board

        # Add any manually specified boards
        if isinstance(manual_boards, list):
            for manual_port in manual_boards:
                # Create board identity from the info given
                initial_identity = BoardIdentity(
                    board_type='manual',
                    asset_tag=manual_port,
                )

                try:
                    board = Arduino(manual_port, initial_identity)
                except BoardDisconnectionError:
                    logger.warning(
                        f"Manually specified arduino at port {manual_port!r}, "
                        "could not be identified. Ignoring this device")
                    continue
                except IncorrectBoardError as err:
                    logger.warning(
                        f"Board returned type {err.returned_type!r}, "
                        f"expected {err.expected_type!r}. Ignoring this device")
                    continue
                boards[board._identity.asset_tag] = board
        return MappingProxyType(boards)

    @log_to_debug
    def identify(self) -> BoardIdentity:
        """
        Get the identity of the board.

        The asset tag of the board is the serial number from the USB descriptor.

        :return: The identity of the board.
        """
        response = self._serial.query('*IDN?')
        response_fields = response.split(':')

        # The arduino firmware cannot access the serial number reported in the USB descriptor
        return BoardIdentity(
            manufacturer=response_fields[0],
            board_type=response_fields[1],
            asset_tag=self._serial_num,
            sw_version=response_fields[3],
        )

    @property
    @log_to_debug
    def pins(self) -> tuple[Pin, ...]:
        """
        The pins on the Arduino.

        :return: A tuple of the pins on the Arduino.
        """
        return self._pins

    @log_to_debug
    def ultrasound_measure(
        self,
        pulse_pin: int,
        echo_pin: int,
    ) -> int:
        """
        Measure the distance to an object using an ultrasound sensor.

        The sensor can only measure distances up to 4m.

        :param pulse_pin: The pin to send the ultrasound pulse from.
        :param echo_pin: The pin to read the ultrasound echo from.
        :raises ValueError: If either of the pins are invalid
        :return: The distance measured by the ultrasound sensor in mm.
        """
        try:  # bounds check
            self.pins[pulse_pin]._check_if_disabled()  # noqa: SLF001
        except (IndexError, IOError):
            raise ValueError("Invalid pulse pin provided") from None
        try:
            self.pins[echo_pin]._check_if_disabled()  # noqa: SLF001
        except (IndexError, IOError):
            raise ValueError("Invalid echo pin provided") from None

        response = self._serial.query(f'ULTRASOUND:{pulse_pin}:{echo_pin}:MEASURE?')
        return int(response)

    def __repr__(self) -> str:
        return f"<{self.__class__.__qualname__}: {self._serial}>"


class Pin:
    """
    A pin on the Arduino.

    :param serial: The serial wrapper to use to communicate with the board.
    :param index: The index of the pin.
    :param supports_analog: Whether the pin supports analog reads.
    """

    __slots__ = ('_disabled', '_index', '_serial', '_supports_analog')

    def __init__(
        self,
        serial: SerialWrapper,
        index: int,
        supports_analog: bool,
        disabled: bool = False
    ):
        self._serial = serial
        self._index = index
        self._supports_analog = supports_analog
        self._disabled = disabled

    @property
    @log_to_debug
    def mode(self) -> GPIOPinMode:
        """
        Get the mode of the pin.

        This is fetched from the board.

        :raises IOError: If this pin cannot be controlled.
        :return: The mode of the pin.
        """
        self._check_if_disabled()
        mode = self._serial.query(f'PIN:{self._index}:MODE:GET?')
        return GPIOPinMode(mode)

    @mode.setter
    @log_to_debug
    def mode(self, value: GPIOPinMode) -> None:
        """
        Set the mode of the pin.

        To do analog or digital reads set the mode to INPUT or INPUT_PULLUP.
        To do digital writes set the mode to OUTPUT.

        :param value: The mode to set the pin to.
        :raises IOError: If the pin mode is not a GPIOPinMode.
        :raises IOError: If this pin cannot be controlled.
        """
        self._check_if_disabled()
        if not isinstance(value, GPIOPinMode):
            raise IOError('Pin mode only supports being set to a GPIOPinMode')
        self._serial.write(f'PIN:{self._index}:MODE:SET:{value.value}')

    @property
    @log_to_debug
    def digital_value(self) -> bool:
        """
        Perform a digital read on the pin.

        :raises IOError: If the pin's current mode does not support digital read
        :raises IOError: If this pin cannot be controlled.
        :return: The digital value of the pin.
        """
        self._check_if_disabled()
        response = self._serial.query(f'PIN:{self._index}:DIGITAL:GET?')
        return (response == '1')

    @digital_value.setter
    @log_to_debug
    def digital_value(self, value: bool) -> None:
        """
        Write a digital value to the pin.

        :param value: The value to write to the pin.
        :raises IOError: If the pin's current mode does not support digital write.
        :raises IOError: If this pin cannot be controlled.
        """
        self._check_if_disabled()
        try:
            if value:
                self._serial.write(f'PIN:{self._index}:DIGITAL:SET:1')
            else:
                self._serial.write(f'PIN:{self._index}:DIGITAL:SET:0')
        except RuntimeError as e:
            if 'is not supported in' in str(e):
                raise IOError(str(e))

    @property
    @log_to_debug
    def analog_value(self) -> float:
        """
        Get the analog voltage on the pin.

        This is returned in volts. Only pins A0-A5 support analog reads.

        :raises IOError: If the pin or its current mode does not support analog read.
        :raises IOError: If this pin cannot be controlled.
        :return: The analog voltage on the pin, ranges from 0 to 5.
        """
        ADC_MAX = 1023  # 10 bit ADC
        ADC_MIN = 0

        self._check_if_disabled()
        if not self._supports_analog:
            raise IOError('Pin does not support analog read')
        try:
            response = self._serial.query(f'PIN:{self._index}:ANALOG:GET?')
        except RuntimeError as e:
            # The firmware returns a NACK if the pin is not in INPUT mode
            if 'is not supported in' in str(e):
                raise IOError(str(e))
        # map the response from the ADC range to the voltage range
        return map_to_float(int(response), ADC_MIN, ADC_MAX, 0.0, 5.0)

    def _check_if_disabled(self) -> None:
        """
        Check if the pin is disabled.

        :raises IOError: If the pin is disabled.
        """
        if self._disabled:
            raise IOError('This pin cannot be controlled.')

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__qualname__} "
            f"index={self._index} analog={self._supports_analog} "
            f"disabled={self._disabled} {self._serial}>"
        )


# PIN:<n>:MODE:GET?
# PIN:<n>:MODE:SET:<value>
# PIN:<n>:DIGITAL:GET?
# PIN:<n>:DIGITAL:SET:<1/0>
# PIN:<n>:ANALOG:GET?
# ULTRASOUND:<pulse>:<echo>:MEASURE?

if __name__ == '__main__':  # pragma: no cover
    arduinos = Arduino._get_supported_boards()  # noqa: SLF001
    for serial_num, board in arduinos.items():
        print(serial_num)

        board.pins[4].mode = GPIOPinMode.INPUT
        board.pins[4].mode = GPIOPinMode.INPUT_PULLUP

        # Digital write
        board.pins[13].mode = GPIOPinMode.OUTPUT
        board.pins[13].digital_value = True
        digital_write_value = board.pins[13].digital_value
        print(f'Set pin 13 to output and set to {digital_write_value}')

        # Digital read
        board.pins[4].mode = GPIOPinMode.INPUT
        digital_read_value = board.pins[4].digital_value
        print(f'Input 4 = {digital_read_value}')

        board.pins[5].mode = GPIOPinMode.INPUT_PULLUP
        digital_read_value = board.pins[5].digital_value
        print(f'Input 5 = {digital_read_value}')

        # Analog read
        board.pins[AnalogPins.A0].mode = GPIOPinMode.INPUT
        analog_read_value = board.pins[AnalogPins.A0].analog_value
        print(f'Analog input A0 = {analog_read_value}')

        # Trigger pin: 4
        # Echo pin: 5
        ultrasound_dist = board.ultrasound_measure(4, 5)
        print(f'Ultrasound distance = {ultrasound_dist}mm')

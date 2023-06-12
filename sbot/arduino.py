from __future__ import annotations

import logging
from enum import Enum, IntEnum
from types import MappingProxyType

from serial.tools.list_ports import comports

from .exceptions import BoardDisconnectionError, IncorrectBoardError
from .logging import log_to_debug
from .serial_wrapper import SerialWrapper
from .utils import Board, BoardIdentity, get_USB_identity, map_to_float

logger = logging.getLogger(__name__)


class GPIOPinMode(str, Enum):
    INPUT = 'INPUT'
    INPUT_PULLUP = 'INPUT_PULLUP'
    OUTPUT = 'OUTPUT'


class AnalogPins(IntEnum):
    A0 = 14
    A1 = 15
    A2 = 16
    A3 = 17
    A4 = 18
    A5 = 19


class Arduino(Board):
    BOARD_TYPE = 'Arduino'
    __supported_vid_pids__ = {
        (0x2341, 0x0043),
        (0x2A03, 0x0043),
        (0x1A86, 0x7523),  # Uno
        (0x10C4, 0xEA60),  # Ruggeduino
        (0x16D0, 0x0613),  # Ruggeduino
    }

    def __init__(
        self,
        serial_port: str,
        initial_identity: BoardIdentity | None = None,
    ) -> None:
        if initial_identity is None:
            initial_identity = BoardIdentity()
        self._serial_num = initial_identity.asset_tag
        self._serial = SerialWrapper(
            serial_port,
            115200,
            identity=initial_identity,
            delay_after_connect=2,
        )

        self._pins = (
            tuple(Pin(self._serial, index, supports_analog=False) for index in range(14))
            + tuple(Pin(self._serial, index, supports_analog=True) for index in range(14, 20))
        )

        self._identity = self.identify()
        if self._identity.board_type != self.BOARD_TYPE:
            raise IncorrectBoardError(self._identity.board_type, self.BOARD_TYPE)
        self._serial.set_identity(self._identity)

    @classmethod
    def _get_supported_boards(cls) -> MappingProxyType[str, Arduino]:
        boards = {}
        serial_ports = comports()
        for port in serial_ports:
            if (port.vid, port.pid) in cls.__supported_vid_pids__:
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
        return MappingProxyType(boards)

    @log_to_debug
    def identify(self) -> BoardIdentity:
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
        return self._pins

    @log_to_debug
    def ultrasound_measure(
        self,
        pulse_pin: int | AnalogPins,
        echo_pin: int | AnalogPins
    ) -> int:
        try:  # bounds check
            _ = self.pins[pulse_pin]
            _ = self.pins[echo_pin]
        except IndexError:
            raise ValueError("Invalid pins provided") from None

        response = self._serial.query(f'ULTRASOUND:{pulse_pin}:{echo_pin}:MEASURE?')
        return int(response)

    def __repr__(self) -> str:
        return f"<{self.__class__.__qualname__}: {self._serial}>"


class Pin:
    _digital_read_modes = (GPIOPinMode.INPUT, GPIOPinMode.INPUT_PULLUP, GPIOPinMode.OUTPUT)
    _digital_write_modes = (GPIOPinMode.OUTPUT)
    _analog_read_modes = (GPIOPinMode.INPUT)

    def __init__(self, serial: SerialWrapper, index: int, supports_analog: bool):
        self._serial = serial
        self._index = index
        self._supports_analog = supports_analog

    @property
    @log_to_debug
    def mode(self) -> GPIOPinMode:
        mode = self._serial.query(f'PIN:{self._index}:MODE:GET?')
        return GPIOPinMode(mode)

    @mode.setter
    @log_to_debug
    def mode(self, value: GPIOPinMode) -> None:
        if not isinstance(value, GPIOPinMode):
            raise IOError('Pin mode only supports being set to a GPIOPinMode')
        self._serial.write(f'PIN:{self._index}:MODE:SET:{value}')

    @property
    @log_to_debug
    def digital_value(self) -> bool:
        if self.mode not in self._digital_read_modes:
            raise IOError(f'Digital read is not supported in {self.mode}')
        response = self._serial.query(f'PIN:{self._index}:DIGITAL:GET?')
        return (response == '1')

    @digital_value.setter
    @log_to_debug
    def digital_value(self, value: bool) -> None:
        if self.mode not in self._digital_write_modes:
            raise IOError(f'Digital write is not supported in {self.mode}')
        if value:
            self._serial.write(f'PIN:{self._index}:DIGITAL:SET:1')
        else:
            self._serial.write(f'PIN:{self._index}:DIGITAL:SET:0')

    @property
    @log_to_debug
    def analog_value(self) -> float:
        """Get the analog voltage on a pin, ranges from 0 to 5."""
        if self.mode not in self._analog_read_modes:
            raise IOError(f'Analog read is not supported in {self.mode}')
        if not self._supports_analog:
            raise IOError('Pin does not support analog read')
        response = self._serial.query(f'PIN:{self._index}:ANALOG:GET?')
        return map_to_float(int(response), 0, 1023, 0.0, 5.0)

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__qualname__} "
            f"index={self._index} analog={self._supports_analog} {self._serial}>"
        )


# PIN:<n>:MODE:GET?
# PIN:<n>:MODE:SET:<value>
# PIN:<n>:DIGITAL:GET?
# PIN:<n>:DIGITAL:SET:<1/0>
# PIN:<n>:ANALOG:GET?
# ULTRASOUND:<pulse>:<echo>:MEASURE?

if __name__ == '__main__':
    arduinos = Arduino._get_supported_boards()
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

        # # Trigger pin: 4
        # # Echo pin: 5
        # ultrasound_sensor = board.setup_ultrasound(4, 5)
        # time_taken = ultrasound_sensor.measure()

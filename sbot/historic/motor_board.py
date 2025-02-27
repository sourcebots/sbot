"""The motor board module provides an interface to the motor board firmware over serial."""
from __future__ import annotations

import atexit
import logging
from enum import IntEnum
from types import MappingProxyType
from typing import NamedTuple

from serial.tools.list_ports import comports

from ..internal.exceptions import BoardDisconnectionError, IncorrectBoardError
from ..internal.logging import log_to_debug
from ..internal.serial_wrapper import SerialWrapper
from .utils import (
    IN_SIMULATOR,
    Board,
    BoardIdentity,
    float_bounds_check,
    get_simulator_boards,
    get_USB_identity,
    map_to_float,
    map_to_int,
)

logger = logging.getLogger(__name__)
BAUDRATE = 115200


class MotorPower(IntEnum):
    """Special values for motor power."""

    BRAKE = 0
    COAST = -1024  # A value outside the allowable range


class MotorStatus(NamedTuple):
    """A tuple representing the status of the motor board."""

    output_faults: tuple[bool, ...]
    input_voltage: float
    other: list[str] = []  # noqa: RUF012

    @classmethod
    def from_status_response(cls, response: str) -> MotorStatus:
        """
        Create a MotorStatus object from the response to a status command.

        :param response: The response from a *STATUS? command.
        :raise TypeError: If the response is invalid.
        :return: A MotorStatus object.
        """
        output_fault_str, input_voltage_mv, *other = response.split(':')
        output_faults = tuple((port == '1') for port in output_fault_str.split(','))
        input_voltage = float(input_voltage_mv) / 1000
        return cls(output_faults, input_voltage, other)


class MotorBoard(Board):
    """
    A class representing the motor board interface.

    This class is intended to be used to communicate with the motor board over serial
    using the text-based protocol added in version 4.4 of the motor board firmware.

    :param serial_port: The serial port to connect to.
    :param initial_identity: The identity of the board, as reported by the USB descriptor.
    """

    __slots__ = ('_identity', '_motors', '_serial')

    @staticmethod
    def get_board_type() -> str:
        """
        Return the type of the board.

        :return: The literal string 'MCv4B'.
        """
        return 'MCv4B'

    def __init__(
        self,
        serial_port: str,
        initial_identity: BoardIdentity | None = None,
    ) -> None:
        if initial_identity is None:
            initial_identity = BoardIdentity()
        self._serial = SerialWrapper(serial_port, BAUDRATE, identity=initial_identity)

        self._motors = (
            Motor(self._serial, 0),
            Motor(self._serial, 1)
        )

        self._identity = self.identify()
        if self._identity.board_type != self.get_board_type():
            raise IncorrectBoardError(self._identity.board_type, self.get_board_type())
        self._serial.set_identity(self._identity)

        # Disable motors on exit
        atexit.register(self._cleanup)

    @classmethod
    def _get_simulator_boards(cls) -> MappingProxyType[str, MotorBoard]:
        """
        Get the simulator boards.

        :return: A mapping of board serial numbers to boards.
        """
        boards = {}
        # The filter here is the name of the emulated board in the simulator
        for board_info in get_simulator_boards('MotorBoard'):

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
                    f"Simulator specified motor board at port {board_info.url!r}, "
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
    ) -> MappingProxyType[str, MotorBoard]:
        """
        Find all connected motor boards.

        Ports are filtered to the USB vendor and product ID: 0x0403 and 0x6001 respectively.

        :param manual_boards: A list of manually specified serial ports to also attempt
            to connect to, defaults to None
        :return: A mapping of serial numbers to motor boards.
        """
        if IN_SIMULATOR:
            return cls._get_simulator_boards()

        boards = {}
        serial_ports = comports()
        for port in serial_ports:
            # Filter to USB vendor and product ID of the FTDI FT232R
            # chip used on the motor board
            if port.vid == 0x0403 and port.pid == 0x6001:
                # Create board identity from USB port info
                initial_identity = get_USB_identity(port)

                try:
                    board = MotorBoard(port.device, initial_identity)
                except BoardDisconnectionError:
                    logger.warning(
                        f"Found motor board-like serial port at {port.device!r}, "
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
                    board = MotorBoard(manual_port, initial_identity)
                except BoardDisconnectionError:
                    logger.warning(
                        f"Manually specified motor board at port {manual_port!r}, "
                        "could not be identified. Ignoring this device")
                    continue
                except IncorrectBoardError as err:
                    logger.warning(
                        f"Board returned type {err.returned_type!r}, "
                        f"expected {err.expected_type!r}. Ignoring this device")
                    continue
                boards[board._identity.asset_tag] = board
        return MappingProxyType(boards)

    @property
    @log_to_debug
    def motors(self) -> tuple[Motor, Motor]:
        """
        A tuple of the two motors on the board.

        :return: A tuple of the two motors on the board.
        """
        return self._motors

    @log_to_debug
    def identify(self) -> BoardIdentity:
        """
        Get the identity of the board.

        :return: The identity of the board.
        """
        response = self._serial.query('*IDN?')
        return BoardIdentity(*response.split(':'))

    @property
    @log_to_debug
    def status(self) -> MotorStatus:
        """
        The status of the board.

        :return: The status of the board.
        """
        response = self._serial.query('*STATUS?')
        return MotorStatus.from_status_response(response)

    @log_to_debug
    def reset(self) -> None:
        """
        Reset the board.

        This command disables the motors and clears all faults.
        """
        self._serial.write('*RESET')

    def _cleanup(self) -> None:
        """
        Disable the motors while exiting.

        This method is registered as an exit handler.
        """
        try:
            self.reset()
        except Exception:
            logger.warning(f"Failed to cleanup motor board {self._identity.asset_tag}.")

    def __repr__(self) -> str:
        return f"<{self.__class__.__qualname__}: {self._serial}>"


class Motor:
    """
    A class representing a motor on the motor board.

    Each motor is controlled through the power property
    and its current can be read using the current property.

    :param serial: The serial wrapper to use to communicate with the board.
    :param index: The index of the motor on the board.
    """

    __slots__ = ('_index', '_serial')

    def __init__(self, serial: SerialWrapper, index: int):
        self._serial = serial
        self._index = index

    @property
    @log_to_debug
    def power(self) -> float:
        """
        Read the current power setting of the motor.

        :return: The power of the motor as a float between -1.0 and 1.0
            or the special value MotorPower.COAST.
        """
        response = self._serial.query(f'MOT:{self._index}:GET?')

        data = response.split(':')
        enabled = (data[0] == '1')
        value = int(data[1])

        if not enabled:
            return MotorPower.COAST
        return map_to_float(value, -1000, 1000, -1.0, 1.0, precision=3)

    @power.setter
    @log_to_debug
    def power(self, value: float) -> None:
        """
        Set the power of the motor.

        Internally this method maps the power to an integer between
        -1000 and 1000 so only 3 digits of precision are available.

        :param value: The power of the motor as a float between -1.0 and 1.0
            or the special values MotorPower.COAST and MotorPower.BRAKE.
        """
        if value == MotorPower.COAST:
            self._serial.write(f'MOT:{self._index}:DISABLE')
            return
        value = float_bounds_check(
            value, -1.0, 1.0,
            'Motor power is a float between -1.0 and 1.0')

        setpoint = map_to_int(value, -1.0, 1.0, -1000, 1000)
        self._serial.write(f'MOT:{self._index}:SET:{setpoint}')

    @property
    @log_to_debug
    def current(self) -> float:
        """
        Read the current draw of the motor.

        :return: The current draw of the motor in amps.
        """
        response = self._serial.query(f'MOT:{self._index}:I?')
        return float(response) / 1000

    @property
    @log_to_debug
    def in_fault(self) -> bool:
        """
        Check if the motor is in a fault state.

        :return: True if the motor is in a fault state, False otherwise.
        """
        response = self._serial.query('*STATUS?')
        return MotorStatus.from_status_response(response).output_faults[self._index]

    def __repr__(self) -> str:
        return f"<{self.__class__.__qualname__} index={self._index} {self._serial}>"


if __name__ == '__main__':  # pragma: no cover
    motorboards = MotorBoard._get_supported_boards()  # noqa: SLF001
    for serial_num, board in motorboards.items():
        print(serial_num)
        print(board.identify())

"""The servo board module provides an interface to the servo board firmware over serial."""
from __future__ import annotations

import atexit
import logging
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

DUTY_MIN = 300
DUTY_MAX = 4000
START_DUTY_MIN = 350
START_DUTY_MAX = 1980
NUM_SERVOS = 8

logger = logging.getLogger(__name__)
BAUDRATE = 115200  # Since the servo board is a USB device, this is ignored


class ServoStatus(NamedTuple):
    """A named tuple containing the values of the servo status output."""

    watchdog_failed: bool
    power_good: bool

    @classmethod
    def from_status_response(cls, response: str) -> ServoStatus:
        """
        Create a ServoStatus from a status response.

        :param response: The response from a *STATUS? command.
        :return: The ServoStatus.
        """
        data = response.split(':')

        return cls(
            watchdog_failed=(data[0] == '1'),
            power_good=(data[1] == '1'),
        )


class ServoBoard(Board):
    """
    A class representing the servo board interface.

    This class is intended to be used to communicate with the servo board over serial
    using the text-based protocol added in version 4.3 of the servo board firmware.

    :param serial_port: The serial port to connect to.
    :param initial_identity: The identity of the board, as reported by the USB descriptor.
    """

    __slots__ = ('_identity', '_serial', '_servos')

    @staticmethod
    def get_board_type() -> str:
        """
        Return the type of the board.

        :return: The literal string 'SBv4B'.
        """
        return 'SBv4B'

    def __init__(
        self,
        serial_port: str,
        initial_identity: BoardIdentity | None = None,
    ) -> None:
        if initial_identity is None:
            initial_identity = BoardIdentity()
        self._serial = SerialWrapper(serial_port, BAUDRATE, identity=initial_identity)

        self._servos = tuple(
            Servo(self._serial, index) for index in range(NUM_SERVOS)
        )

        self._identity = self.identify()
        if self._identity.board_type != self.get_board_type():
            raise IncorrectBoardError(self._identity.board_type, self.get_board_type())
        self._serial.set_identity(self._identity)

        atexit.register(self._cleanup)

    @classmethod
    def _get_simulator_boards(cls) -> MappingProxyType[str, ServoBoard]:
        """
        Get the simulator boards.

        :return: A mapping of board serial numbers to boards.
        """
        boards = {}
        # The filter here is the name of the emulated board in the simulator
        for board_info in get_simulator_boards('ServoBoard'):

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
                    f"Simulator specified servo board at port {board_info.url!r}, "
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
    ) -> MappingProxyType[str, 'ServoBoard']:
        """
        Find all connected servo boards.

        Ports are filtered to the USB vendor and product ID: 0x1BDA and 0x0011 respectively.

        :param manual_boards: A list of manually specified serial ports to also attempt
            to connect to, defaults to None
        :return: A mapping of serial numbers to servo boards.
        """
        if IN_SIMULATOR:
            return cls._get_simulator_boards()

        boards = {}
        serial_ports = comports()
        for port in serial_ports:
            # Filter to USB vendor and product ID of the SR v4 servo board
            if port.vid == 0x1BDA and port.pid == 0x0011:
                # Create board identity from USB port info
                initial_identity = get_USB_identity(port)

                try:
                    board = ServoBoard(port.device, initial_identity)
                except BoardDisconnectionError:
                    logger.warning(
                        f"Found servo board-like serial port at {port.device!r}, "
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
                    board = ServoBoard(manual_port, initial_identity)
                except BoardDisconnectionError:
                    logger.warning(
                        f"Manually specified servo board at port {manual_port!r}, "
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
    def servos(self) -> tuple['Servo', ...]:
        """
        A tuple of the servos on the board.

        :return: A tuple of the servos on the board.
        """
        return self._servos

    @log_to_debug
    def identify(self) -> BoardIdentity:
        """
        Get the identity of the board.

        :return: The identity of the board.
        """
        response = self._serial.query('*IDN?')
        return BoardIdentity(*response.split(':'))

    @log_to_debug
    def status(self) -> ServoStatus:
        """
        Get the board's status.

        :return: A named tuple of the watchdog fail and pgood status.
        """
        response = self._serial.query('*STATUS?')

        return ServoStatus.from_status_response(response)

    @log_to_debug
    def reset(self) -> None:
        """
        Reset the board.

        This will disable all servos.
        """
        self._serial.write('*RESET')

    @property
    @log_to_debug
    def current(self) -> float:
        """
        Get the current draw of the board.

        This only includes the servos powered through the main port, not the aux port.

        :return: The current draw of the board in amps.
        """
        response = self._serial.query('SERVO:I?')
        return float(response) / 1000

    @property
    @log_to_debug
    def voltage(self) -> float:
        """
        Get the voltage of the on-board regulator.

        :return: The voltage of the on-board regulator in volts.
        """
        response = self._serial.query('SERVO:V?')
        return float(response) / 1000

    def _cleanup(self) -> None:
        """
        Reset the board and disable all servos on exit.

        This is registered as an exit function.
        """
        try:
            self.reset()
        except Exception:
            logger.warning(f"Failed to cleanup servo board {self._identity.asset_tag}.")

    def __repr__(self) -> str:
        return f"<{self.__class__.__qualname__}: {self._serial}>"


class Servo:
    """
    A class representing a servo on the servo board.

    :param serial: The serial wrapper to use to communicate with the board.
    :param index: The index of the servo on the board.
    """

    __slots__ = ('_duty_max', '_duty_min', '_index', '_serial')

    def __init__(self, serial: SerialWrapper, index: int):
        self._serial = serial
        self._index = index

        self._duty_min = START_DUTY_MIN
        self._duty_max = START_DUTY_MAX

    @log_to_debug
    def set_duty_limits(self, lower: int, upper: int) -> None:
        """
        Set the pulse on-time limits of the servo.

        These limits are used to map the servo position to a pulse on-time.

        :param lower: The lower limit of the servo pulse in μs.
        :param upper: The upper limit of the servo pulse in μs.
        :raises TypeError: If the limits are not ints.
        :raises ValueError: If the limits are not in the range 500 to 4000.
        """
        if not (isinstance(lower, int) and isinstance(upper, int)):
            raise TypeError(
                f'Servo pulse limits are ints in μs, in the range {DUTY_MIN} to {DUTY_MAX}'
            )
        if not (DUTY_MIN <= lower <= DUTY_MAX and DUTY_MIN <= upper <= DUTY_MAX):
            raise ValueError(
                f'Servo pulse limits are ints in μs, in the range {DUTY_MIN} to {DUTY_MAX}'
            )

        self._duty_min = lower
        self._duty_max = upper

    @log_to_debug
    def get_duty_limits(self) -> tuple[int, int]:
        """
        Get the current pulse on-time limits of the servo.

        The limits are specified in μs.

        :return: A tuple of the lower and upper limits of the servo pulse in μs.
        """
        return self._duty_min, self._duty_max

    @property
    @log_to_debug
    def position(self) -> float | None:
        """
        Get the position of the servo.

        If the servo is disabled, this will return None.

        :return: The position of the servo as a float between -1.0 and 1.0 or None if disabled.
        """
        response = self._serial.query(f'SERVO:{self._index}:GET?')
        data = int(response)
        if data == 0:
            return None
        return map_to_float(data, self._duty_min, self._duty_max, -1.0, 1.0, precision=3)

    @position.setter
    @log_to_debug
    def position(self, value: float | None) -> None:
        """
        Set the position of the servo.

        If the servo is disabled, this will enable it.
        -1.0 to 1.0 may not be the full range of the servo, see set_duty_limits().

        :param value: The position of the servo as a float between -1.0 and 1.0
            or None to disable.
        """
        if value is None:
            self.disable()
            return
        value = float_bounds_check(
            value, -1.0, 1.0,
            'Servo position is a float between -1.0 and 1.0')

        setpoint = map_to_int(value, -1.0, 1.0, self._duty_min, self._duty_max)
        self._serial.write(f'SERVO:{self._index}:SET:{setpoint}')

    @log_to_debug
    def disable(self) -> None:
        """
        Disable the servo.

        This will cause this channel to output a 0% duty cycle.
        """
        self._serial.write(f'SERVO:{self._index}:DISABLE')

    def __repr__(self) -> str:
        return f"<{self.__class__.__qualname__} index={self._index} {self._serial}>"


if __name__ == '__main__':  # pragma: no cover
    servoboards = ServoBoard._get_supported_boards()  # noqa: SLF001
    for serial_num, board in servoboards.items():
        print(serial_num)
        print(board.identify())

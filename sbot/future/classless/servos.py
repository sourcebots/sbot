"""The interface for a single servo board output over serial."""
from __future__ import annotations

from collections import defaultdict
from typing import NamedTuple

from sbot.logging import log_to_debug
from sbot.serial_wrapper import SerialWrapper
from sbot.utils import float_bounds_check, map_to_float, map_to_int

from .utils import BoardIdentifier, BoardManager

DUTY_MIN = 300
DUTY_MAX = 4000
START_DUTY_MIN = 350
START_DUTY_MAX = 1980
NUM_SERVOS = 8


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


class Servo:
    """
    A class representing a single servo board output.

    This class is intended to be used to communicate with the servo board over serial
    using the text-based protocol added in version 4.3 of the servo board firmware.

    :param boards: The BoardManager object containing the servo board references.
    """

    __slots__ = ('_duty_limits', '_outputs')

    def __init__(self, boards: BoardManager):
        self._outputs = boards.servos

        self._duty_limits: dict[int, tuple[int, int]] = defaultdict(
            lambda: (START_DUTY_MIN, START_DUTY_MAX),
        )

    @log_to_debug
    def set_duty_limits(self, id: int, lower: int, upper: int) -> None:
        """
        Set the pulse on-time limits of the servo.

        These limits are used to map the servo position to a pulse on-time.

        :param id: The ID of the servo.
        :param lower: The lower limit of the servo pulse in μs.
        :param upper: The upper limit of the servo pulse in μs.
        :raises TypeError: If the limits are not ints.
        :raises ValueError: If the limits are not in the range 300 to 4000.
        """
        # Validate output exists
        _output = self._find_output(id)

        if not (isinstance(lower, int) and isinstance(upper, int)):
            raise TypeError(
                f'Servo pulse limits are ints in μs, in the range {DUTY_MIN} to {DUTY_MAX}'
            )
        if not (DUTY_MIN <= lower <= DUTY_MAX and DUTY_MIN <= upper <= DUTY_MAX):
            raise ValueError(
                f'Servo pulse limits are ints in μs, in the range {DUTY_MIN} to {DUTY_MAX}'
            )

        self._duty_limits[id] = (lower, upper)

    @log_to_debug
    def get_duty_limits(self, id: int) -> tuple[int, int]:
        """
        Get the current pulse on-time limits of the servo.

        The limits are specified in μs.

        :param id: The ID of the servo.
        :return: A tuple of the lower and upper limits of the servo pulse in μs.
        """
        return self._duty_limits[id]

    @log_to_debug
    def set_position(self, id: int, position: float) -> None:
        """
        Set the position of the servo.

        If the servo is disabled, this will enable it.
        -1.0 to 1.0 may not be the full range of the servo, see set_duty_limits().

        :param position: The position of the servo as a float between -1.0 and 1.0
        """
        output = self._find_output(id)
        position = float_bounds_check(
            position, -1.0, 1.0,
            'Servo position is a float between -1.0 and 1.0')

        duty_min, duty_max = self._duty_limits[id]

        setpoint = map_to_int(position, -1.0, 1.0, duty_min, duty_max)
        output.port.write(f'SERVO:{output.idx}:SET:{setpoint}')

    @log_to_debug
    def get_position(self, id: int) -> float | None:
        """
        Get the position of the servo.

        If the servo is disabled, this will return None.

        :return: The position of the servo as a float between -1.0 and 1.0 or None if disabled.
        """
        output = self._find_output(id)
        response = output.port.query(f'SERVO:{output.idx}:GET?')
        data = int(response)
        if data == 0:
            return None
        duty_min, duty_max = self._duty_limits[id]
        return map_to_float(data, duty_min, duty_max, -1.0, 1.0, precision=3)

    @log_to_debug
    def disable(self, id: int) -> None:
        """
        Disable the servo.

        This will cause this channel to output a 0% duty cycle.

        :param id: The ID of the servo.
        """
        output = self._find_output(id)
        output.port.write(f'SERVO:{output.idx}:DISABLE')

    @log_to_debug
    def status(self, id: int) -> ServoStatus:
        """
        The status of the board the servo is connected to.

        :param id: The ID of the servo.
        :return: A named tuple of the watchdog fail and pgood status.
        """
        output = self._find_output(id)
        response = output.port.query('*STATUS?')

        return ServoStatus.from_status_response(response)

    @log_to_debug
    def reset(self) -> None:
        """
        Reset all servo boards.

        This will disable all servos.
        """
        for board in self._get_boards():
            board.write('*RESET')

    @log_to_debug
    def get_current(self, id: int) -> float:
        """
        Get the current draw of the servo board the servo is connected to.

        This only includes the servos powered through the main port, not the aux port.

        :return: The current draw of the board in amps.
        """
        output = self._find_output(id)
        response = output.port.query('SERVO:I?')
        return float(response) / 1000

    @log_to_debug
    def get_voltage(self, id: int) -> float:
        """
        Get the voltage of the on-board regulator.

        :param id: The ID of the servo.
        :return: The voltage of the on-board regulator in volts.
        """
        output = self._find_output(id)
        response = output.port.query('SERVO:V?')
        return float(response) / 1000

    def _find_output(self, id: int) -> BoardIdentifier:
        try:
            return self._outputs[id]
        except IndexError:
            raise ValueError(f"Output {id} does not exist")

    def _get_boards(self) -> list[SerialWrapper]:
        unique_boards = []
        for output in self._outputs:
            if output.port not in unique_boards:
                unique_boards.append(output.port)
        return unique_boards

    def __repr__(self) -> str:
        board_ports = self._get_boards()
        return f"<{self.__class__.__qualname__} {board_ports}>"

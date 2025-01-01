"""The interface for a single motor board output over serial."""
from __future__ import annotations

from enum import IntEnum
from typing import ClassVar, NamedTuple

from sbot.logging import log_to_debug
from sbot.serial_wrapper import SerialWrapper
from sbot.utils import float_bounds_check, map_to_float, map_to_int

from .utils import BoardIdentifier, BoardManager


class MotorPower(IntEnum):
    """Special values for motor power."""

    BRAKE = 0
    COAST = -1024  # A value outside the allowable range


class MotorStatus(NamedTuple):
    """A tuple representing the status of the motor board."""

    output_faults: tuple[bool, ...]
    input_voltage: float
    other: ClassVar[list[str]] = []

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


class Motor:
    """
    A class representing a single motor board output.

    This class is intended to be used to communicate with the motor board over serial
    using the text-based protocol added in version 4.4 of the motor board firmware.

    :param boards: The BoardManager object containing the motor board references.
    """

    __slots__ = ('_outputs',)

    def __init__(self, boards: BoardManager):
        # Obtain a reference to the list of output ports
        # This may not have been populated yet
        self._outputs = boards.motors

    @log_to_debug
    def set_power(self, id: int, power: float) -> None:
        """
        Set the power of the motor.

        Internally this method maps the power to an integer between
        -1000 and 1000 so only 3 digits of precision are available.

        :param id: The ID of the motor.
        :param value: The power of the motor as a float between -1.0 and 1.0
            or the special values MotorPower.COAST and MotorPower.BRAKE.
        """
        output = self._find_output(id)
        if power == MotorPower.COAST:
            output.port.write(f'MOT:{output.idx}:DISABLE')
            return
        power = float_bounds_check(
            power, -1.0, 1.0,
            'Motor power is a float between -1.0 and 1.0')

        setpoint = map_to_int(power, -1.0, 1.0, -1000, 1000)
        output.port.write(f'MOT:{output.idx}:SET:{setpoint}')

    @log_to_debug
    def get_power(self, id: int) -> float:
        """
        Read the current power setting of the motor.

        :param id: The ID of the motor.
        :return: The power of the motor as a float between -1.0 and 1.0
            or the special value MotorPower.COAST.
        """
        output = self._find_output(id)
        response = output.port.query(f'MOT:{output.idx}:GET?')

        data = response.split(':')
        enabled = (data[0] == '1')
        value = int(data[1])

        if not enabled:
            return MotorPower.COAST
        return map_to_float(value, -1000, 1000, -1.0, 1.0, precision=3)

    @log_to_debug
    def status(self, id: int) -> MotorStatus:
        """
        The status of the board the motor is connected to.

        :param id: The ID of the motor.
        :return: The status of the board.
        """
        output = self._find_output(id)
        response = output.port.query('*STATUS?')
        return MotorStatus.from_status_response(response)

    @log_to_debug
    def reset(self) -> None:
        """
        Reset attached boards.

        This command disables the motors and clears all faults.
        :raise RuntimeError: If no motor boards are connected.
        """
        boards = self._get_boards()
        for board in boards:
            board.write('*RESET')

    @log_to_debug
    def get_motor_current(self, id: int) -> float:
        """
        Read the current draw of the motor.

        :param id: The ID of the motor.
        :return: The current draw of the motor in amps.
        """
        output = self._find_output(id)
        response = output.port.query(f'MOT:{output.idx}:I?')
        return float(response) / 1000

    @log_to_debug
    def in_fault(self, id: int) -> bool:
        """
        Check if the motor is in a fault state.

        :param id: The ID of the motor.
        :return: True if the motor is in a fault state, False otherwise.
        """
        output = self._find_output(id)
        response = output.port.query('*STATUS?')
        return MotorStatus.from_status_response(response).output_faults[output.idx]

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

"""The interface for a single power board output over serial."""
from __future__ import annotations

from enum import IntEnum
from typing import ClassVar, NamedTuple

from sbot.logging import log_to_debug

from .utils import BoardIdentifier, BoardManager


class PowerOutputPosition(IntEnum):
    """
    A mapping of output name to number of the PowerBoard outputs.

    The numbers here are the same as used in communication protocol with the PowerBoard.
    """

    H0 = 0
    H1 = 1
    L0 = 2
    L1 = 3
    L2 = 4
    L3 = 5
    FIVE_VOLT = 6


class BatteryData(NamedTuple):
    """
    A container for the battery data.

    :param voltage: The voltage of the battery in volts.
    :param current: The current draw of the battery in amps.
    """

    voltage: float
    current: float


class PowerStatus(NamedTuple):
    """
    A named tuple containing the values of the power status output.

    :param overcurrent: A tuple of booleans indicating whether each output is
        in an overcurrent state.
    :param temperature: The temperature of the power board in degrees Celsius.
    :param fan_running: Whether the fan is running.
    :param regulator_voltage: The voltage of the regulator in volts.
    :param other: A list of any other values returned by the status command.
    """

    overcurrent: tuple[bool, ...]
    temperature: int
    fan_running: bool
    regulator_voltage: float
    other: ClassVar[list[str]] = []

    @classmethod
    def from_status_response(cls, response: str) -> PowerStatus:
        """
        Create a PowerStatus object from the response to a status command.

        :param response: The response from a *STATUS? command.
        :raise TypeError: If the response is invalid.
        :return: A PowerStatus object.
        """
        oc_flags, temp, fan_running, raw_voltage, *other = response.split(':')
        return cls(
            overcurrent=tuple((x == '1') for x in oc_flags.split(',')),
            temperature=int(temp),
            fan_running=(fan_running == '1'),
            regulator_voltage=float(raw_voltage) / 1000,
            other=other,
        )


# This output is always on, and cannot be controlled via the API.
BRAIN_OUTPUT = PowerOutputPosition.L2


class Power:
    """
    A class representing a single power board output.

    This class is intended to be used to communicate with the power board over serial
    using the text-based protocol.

    :param boards: The BoardManager object containing the power board.
    """

    __slots__ = ('_outputs',)

    def __init__(self, boards: BoardManager):
        # Obtain a reference to the list of output ports
        # This may not have been populated yet
        self._outputs = boards.power

    @log_to_debug
    def set_output(self, id: int, on: bool) -> None:
        """
        Set whether the output is enabled.

        Outputs that have been disabled due to overcurrent will not be enabled,
        but will not raise an error.

        :param id: The ID of the output.
        :param value: Whether the output should be enabled.
        """
        output = self._find_output(id)
        if id == BRAIN_OUTPUT:
            # Changing the brain output will also raise a NACK from the firmware
            raise RuntimeError("Brain output cannot be controlled via this API.")
        if on:
            output.port.write(f'OUT:{output.idx}:SET:1')
        else:
            output.port.write(f'OUT:{output.idx}:SET:0')

    @log_to_debug
    def is_output_on(self, id: int) -> bool:
        """
        Return whether the output is enabled.

        Outputs are enabled at startup, but will be disabled if the output draws
        too much current or are switched off by the user.

        :param id: The ID of the output.
        :return: Whether the output is enabled.
        """
        output = self._find_output(id)
        response = output.port.query(f'OUT:{output.idx}:GET?')
        return response == '1'

    @log_to_debug
    def get_output_current(self, id: int) -> float:
        """
        Return the current draw of the output.

        This current measurement has a 10% tolerance.

        :param id: The ID of the output.
        :return: The current draw of the output, in amps.
        """
        output = self._find_output(id)
        response = output.port.query(f'OUT:{output.idx}:I?')
        return float(response) / 1000

    @log_to_debug
    def get_battery_data(self) -> BatteryData:
        """
        Get the battery data from the power board.

        This is implemented using an INA219 current sensor on the power board.

        :return: A BatteryData object containing the voltage and current of the battery.
        :raise RuntimeError: If no power boards are connected.
        """
        output = self._get_power_board()
        volt_response = output.port.query('BATT:V?')
        curr_response = output.port.query('BATT:I?')
        return BatteryData(
            voltage=float(volt_response) / 1000,
            current=float(curr_response) / 1000
        )

    @log_to_debug
    def status(self) -> PowerStatus:
        """
        Return the status of the power board.

        :return: The status of the power board.
        :raise RuntimeError: If no power boards are connected.
        """
        output = self._get_power_board()
        response = output.port.query('*STATUS?')
        return PowerStatus.from_status_response(response)

    @log_to_debug
    def reset(self) -> None:
        """
        Reset the power board.

        This turns off all outputs except the brain output and stops any running tones.
        :raise RuntimeError: If no power boards are connected.
        """
        if len(self._outputs) == 0:
            raise RuntimeError("No power boards connected")
        output = self._outputs[0]
        output.port.write('*RESET')

    def _find_output(self, id: int) -> BoardIdentifier:
        try:
            return self._outputs[id]
        except IndexError:
            raise ValueError(f"Output {id} does not exist")

    def _get_power_board(self) -> BoardIdentifier:
        if len(self._outputs) == 0:
            raise RuntimeError("No power boards connected")
        return self._outputs[0]

    def __repr__(self) -> str:
        try:
            pb = self._get_power_board()
        except RuntimeError:
            return f"<{self.__class__.__qualname__} no power board>"
        else:
            return f"<{self.__class__.__qualname__} {pb.port}>"

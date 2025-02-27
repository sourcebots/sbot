"""The power board module provides an interface to the power board firmware over serial."""
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
)

logger = logging.getLogger(__name__)
BAUDRATE = 115200  # Since the power board is a USB device, this is ignored


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


class PowerStatus(NamedTuple):
    """A named tuple containing the values of the power status output."""

    overcurrent: tuple[bool, ...]
    temperature: int
    fan_running: bool
    regulator_voltage: float
    other: list[str] = []  # noqa: RUF012

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


class PowerBoard(Board):
    """
    A class representing the power board interface.

    This class is intended to be used to communicate with the power board over serial.

    :param serial_port: The serial port to connect to.
    :param initial_identity: The identity of the board, as reported by the USB descriptor.
    """

    __slots__ = (
        '_battery_sensor', '_error_led', '_identity', '_outputs', '_piezo', '_run_led',
        '_serial')

    @staticmethod
    def get_board_type() -> str:
        """
        Return the type of the board.

        :return: The literal string 'PBv4B'.
        """
        return 'PBv4B'

    def __init__(
        self,
        serial_port: str,
        initial_identity: BoardIdentity | None = None,
    ) -> None:
        if initial_identity is None:
            initial_identity = BoardIdentity()
        self._serial = SerialWrapper(serial_port, BAUDRATE, identity=initial_identity)

        self._outputs = Outputs(self._serial)
        self._battery_sensor = BatterySensor(self._serial)
        self._piezo = Piezo(self._serial)
        self._run_led = Led(self._serial, 'RUN')
        self._error_led = Led(self._serial, 'ERR')

        self._identity = self.identify()
        if self._identity.board_type != self.get_board_type():
            raise IncorrectBoardError(self._identity.board_type, self.get_board_type())
        self._serial.set_identity(self._identity)

        atexit.register(self._cleanup)

    @classmethod
    def _get_simulator_boards(cls) -> MappingProxyType[str, PowerBoard]:
        """
        Get the simulator boards.

        :return: A mapping of board serial numbers to boards.
        """
        boards = {}
        # The filter here is the name of the emulated board in the simulator
        for board_info in get_simulator_boards('PowerBoard'):

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
                    f"Simulator specified power board at port {board_info.url!r}, "
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
    ) -> MappingProxyType[str, PowerBoard]:
        """
        Find all connected power boards.

        Ports are filtered to the USB vendor and product ID: 0x1BDA and 0x0010 respectively.

        :param manual_boards: A list of manually specified serial ports to also attempt
            to connect to, defaults to None
        """
        if IN_SIMULATOR:
            return cls._get_simulator_boards()

        boards = {}
        serial_ports = comports()
        for port in serial_ports:
            # Filter to USB vendor and product ID of the SR v4 power board
            if port.vid == 0x1BDA and port.pid == 0x0010:
                # Create board identity from USB port info
                initial_identity = get_USB_identity(port)

                try:
                    board = PowerBoard(port.device, initial_identity)
                except BoardDisconnectionError:
                    logger.warning(
                        f"Found power board-like serial port at {port.device!r}, "
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
                    board = PowerBoard(manual_port, initial_identity)
                except BoardDisconnectionError:
                    logger.warning(
                        f"Manually specified power board at port {manual_port!r}, "
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
    def outputs(self) -> Outputs:
        """
        Return the outputs of the power board.

        :return: The outputs of the power board.
        """
        return self._outputs

    @property
    def battery_sensor(self) -> BatterySensor:
        """
        Return the battery sensor of the power board.

        The battery sensor is used to measure the voltage and total current draw
        from the battery.

        :return: The battery sensor of the power board.
        """
        return self._battery_sensor

    @property
    def piezo(self) -> Piezo:
        """
        Return the piezo of the power board.

        The piezo is used to produce audible tones.

        :return: The piezo of the power board.
        """
        return self._piezo

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
    def status(self) -> PowerStatus:
        """
        Return the status of the power board.

        :return: The status of the power board.
        """
        response = self._serial.query('*STATUS?')
        return PowerStatus.from_status_response(response)

    @log_to_debug
    def reset(self) -> None:
        """
        Reset the power board.

        This turns off all outputs except the brain output and stops any running tones.
        """
        self._serial.write('*RESET')

    def _start_button(self) -> bool:
        """
        Return whether the start button has been pressed.

        This value latches until the button is read, so only shows that the
        button has been pressed since this method was last called.

        :return: Whether the start button has been pressed.
        """
        response: str = self._serial.query('BTN:START:GET?')
        internal, external = response.split(':')
        return (internal == '1') or (external == '1')

    def _cleanup(self) -> None:
        """
        Reset the power board and turn off all outputs when exiting.

        This method is registered as an exit handler and is called to ensure
        the power board is left in a safe state.
        """
        try:
            self.reset()
        except Exception:
            logger.warning("Failed to cleanup power board.")

    def __repr__(self) -> str:
        return f"<{self.__class__.__qualname__}: {self._serial}>"


class Outputs:
    """
    A class representing the outputs of the power board.

    The individual outputs are accessed using the index operator.
    e.g. ``outputs[PowerOutputPosition.H0]``
    This also contains helper methods for controlling all outputs at once.

    :param serial: The serial wrapper to use for communication.
    """

    __slots__ = ('_outputs', '_serial')

    def __init__(self, serial: SerialWrapper):
        self._serial = serial
        self._outputs = tuple(Output(serial, i) for i in range(7))

    def __getitem__(self, key: int) -> Output:
        return self._outputs[key]

    @log_to_debug
    def power_off(self) -> None:
        """
        Turn off all outputs except the brain output.

        This is also used to turn off the outputs when the board is reset.
        """
        for output in self._outputs:
            if output._index == BRAIN_OUTPUT:  # noqa: SLF001
                continue
            output.is_enabled = False

    @log_to_debug
    def power_on(self) -> None:
        """Turn on all outputs."""
        for output in self._outputs:
            if output._index == BRAIN_OUTPUT:  # noqa: SLF001
                continue
            output.is_enabled = True

    def __repr__(self) -> str:
        return f"<{self.__class__.__qualname__}: {self._serial}>"


class Output:
    """
    A class representing a single output of the power board.

    :param serial: The serial wrapper to use for communication.
    :param index: The index of the output to represent.
    """

    __slots__ = ('_index', '_serial')

    def __init__(self, serial: SerialWrapper, index: int):
        self._serial = serial
        self._index = index

    @property
    @log_to_debug
    def is_enabled(self) -> bool:
        """
        Return whether the output is enabled.

        Outputs are enabled at startup, but will be disabled if the output draws
        too much current.

        :return: Whether the output is enabled.
        """
        response = self._serial.query(f'OUT:{self._index}:GET?')
        return response == '1'

    @is_enabled.setter
    @log_to_debug
    def is_enabled(self, value: bool) -> None:
        """
        Set whether the output is enabled.

        Outputs that have been disabled due to overcurrent will not be enabled,
        but will not raise an error.

        :param value: Whether the output should be enabled.
        """
        if self._index == BRAIN_OUTPUT:
            # Changing the brain output will also raise a NACK from the firmware
            raise RuntimeError("Brain output cannot be controlled via this API.")
        if value:
            self._serial.write(f'OUT:{self._index}:SET:1')
        else:
            self._serial.write(f'OUT:{self._index}:SET:0')

    @property
    @log_to_debug
    def current(self) -> float:
        """
        Return the current draw of the output.

        This current measurement has a 10% tolerance.

        :return: The current draw of the output, in amps.
        """
        response = self._serial.query(f'OUT:{self._index}:I?')
        return float(response) / 1000

    @property
    @log_to_debug
    def overcurrent(self) -> bool:
        """
        Return whether the output is in an overcurrent state.

        This is set when the output draws more than its maximum current.
        Resetting the power board will clear this state.

        :return: Whether the output is in an overcurrent state.
        """
        response = self._serial.query('*STATUS?')
        return PowerStatus.from_status_response(response).overcurrent[self._index]

    def __repr__(self) -> str:
        return f"<{self.__class__.__qualname__} index={self._index} {self._serial}>"


class Led:
    """
    A class representing a single LED of the power board.

    :param serial: The serial wrapper to use for communication.
    :param led: The name of the LED to represent.
    """

    __slots__ = ('_led', '_serial')

    def __init__(self, serial: SerialWrapper, led: str):
        self._serial = serial
        self._led = led

    @log_to_debug
    def on(self) -> None:
        """Turn on the LED."""
        self._serial.write(f'LED:{self._led}:SET:1')

    @log_to_debug
    def off(self) -> None:
        """Turn off the LED."""
        self._serial.write(f'LED:{self._led}:SET:0')

    @log_to_debug
    def flash(self) -> None:
        """Set the LED to flash at 1Hz."""
        self._serial.write(f'LED:{self._led}:SET:F')

    def __repr__(self) -> str:
        return f"<{self.__class__.__qualname__} led={self._led} {self._serial}>"


class BatterySensor:
    """
    A class representing the battery sensor of the power board.

    This is implemented using an INA219 current sensor on the power board.

    :param serial: The serial wrapper to use for communication.
    """

    __slots__ = ('_serial',)

    def __init__(self, serial: SerialWrapper):
        self._serial = serial

    @property
    @log_to_debug
    def voltage(self) -> float:
        """
        Return the voltage of the battery.

        :return: The voltage of the battery, in volts.
        """
        response = self._serial.query('BATT:V?')
        return float(response) / 1000

    @property
    @log_to_debug
    def current(self) -> float:
        """
        Return the current draw from the battery.

        :return: The current draw from the battery, in amps.
        """
        response = self._serial.query('BATT:I?')
        return float(response) / 1000

    def __repr__(self) -> str:
        return f"<{self.__class__.__qualname__}: {self._serial}>"


class Piezo:
    """
    A class representing the piezo of the power board.

    The piezo is used to produce audible tones.

    :param serial: The serial wrapper to use for communication.
    """

    __slots__ = ('_serial',)

    def __init__(self, serial: SerialWrapper):
        self._serial = serial

    @log_to_debug
    def buzz(self, frequency: float, duration: float) -> None:
        """
        Produce a tone on the piezo.

        This method is non-blocking, and sending another tone while one is
        playing will cancel the first.

        :param frequency: The frequency of the tone, in Hz.
        :param duration: The duration of the tone, in seconds.
        """
        frequency_int = int(float_bounds_check(
            frequency, 8, 10_000, "Frequency is a float in Hz between 0 and 10000"))
        duration_ms = int(float_bounds_check(
            duration * 1000, 0, 2**31 - 1,
            f"Duration is a float in seconds between 0 and {(2**31 - 1) / 1000:,.0f}"))

        cmd = f'NOTE:{frequency_int}:{duration_ms}'
        self._serial.write(cmd)

    def __repr__(self) -> str:
        return f"<{self.__class__.__qualname__}: {self._serial}>"


class Note(IntEnum):
    """
    An enumeration of notes.

    An enumeration of notes from scientific pitch
    notation and their related frequencies in Hz.
    """

    C6 = 1047
    D6 = 1175
    E6 = 1319
    F6 = 1397
    G6 = 1568
    A6 = 1760
    B6 = 1976
    C7 = 2093
    D7 = 2349
    E7 = 2637
    F7 = 2794
    G7 = 3136
    A7 = 3520
    B7 = 3951
    C8 = 4186

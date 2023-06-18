from __future__ import annotations

import atexit
import logging
from enum import Enum, IntEnum
from types import MappingProxyType

from serial.tools.list_ports import comports

from .exceptions import BoardDisconnectionError, IncorrectBoardError
from .logging import log_to_debug
from .serial_wrapper import SerialWrapper
from .utils import Board, BoardIdentity, float_bounds_check, get_USB_identity

logger = logging.getLogger(__name__)


class PowerOutputPosition(IntEnum):
    """
    A mapping of name to number of the PowerBoard outputs.

    The numbers here are the same as used in wire communication with the PowerBoard.
    """
    H0 = 0
    H1 = 1
    L0 = 2
    L1 = 3
    L2 = 4
    L3 = 5
    FIVE_VOLT = 6


BRAIN_OUTPUT = PowerOutputPosition.FIVE_VOLT


class PowerBoard(Board):
    __slots__ = (
        '_serial', '_identity', '_outputs', '_battery_sensor',
        '_piezo', '_run_led', '_error_led')

    @staticmethod
    def get_board_type() -> str:
        return 'PBv4B'

    def __init__(
        self,
        serial_port: str,
        initial_identity: BoardIdentity | None = None,
    ) -> None:
        if initial_identity is None:
            initial_identity = BoardIdentity()
        self._serial = SerialWrapper(serial_port, 115200, identity=initial_identity)

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
    def _get_supported_boards(
        cls, manual_boards: list[str] | None = None,
    ) -> MappingProxyType[str, PowerBoard]:
        boards = {}
        serial_ports = comports()
        for port in serial_ports:
            if port.vid == 0x1BDA and port.pid == 0x0010:
                # Create board identity from USB port info
                initial_identity = get_USB_identity(port)

                try:
                    board = PowerBoard(port.device, initial_identity)
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
        return self._outputs

    @property
    def battery_sensor(self) -> BatterySensor:
        return self._battery_sensor

    @property
    def piezo(self) -> Piezo:
        return self._piezo

    @log_to_debug
    def identify(self) -> BoardIdentity:
        response = self._serial.query('*IDN?')
        return BoardIdentity(*response.split(':'))

    @property
    @log_to_debug
    def temperature(self) -> int:
        response = self._serial.query('*STATUS?')
        _, temp, *_ = response.split(':')
        return int(temp)

    @property
    @log_to_debug
    def fan(self) -> bool:
        response = self._serial.query('*STATUS?')
        _, _, fan, *_ = response.split(':')
        return True if (fan == '1') else False

    @property
    @log_to_debug
    def regulator_voltage(self) -> float:
        response = self._serial.query('*STATUS?')
        _, _, _, raw_voltage, *_ = response.split(':')
        return float(raw_voltage) / 1000

    @log_to_debug
    def reset(self) -> None:
        self._serial.write('*RESET')

    def _start_button(self) -> bool:
        response: str = self._serial.query('BTN:START:GET?')
        internal, external = response.split(':')
        return (internal == '1') or (external == '1')

    def _cleanup(self) -> None:
        try:
            self.reset()
        except Exception:
            logger.warning("Failed to cleanup power board.")

    def __repr__(self) -> str:
        return f"<{self.__class__.__qualname__}: {self._serial}>"


class Outputs:
    __slots__ = ('_serial', '_outputs')

    def __init__(self, serial: SerialWrapper):
        self._serial = serial
        self._outputs = tuple(Output(serial, i) for i in range(7))

    def __getitem__(self, key: int) -> Output:
        return self._outputs[key]

    @log_to_debug
    def power_off(self) -> None:
        for output in self._outputs:
            if output._index == BRAIN_OUTPUT:
                continue
            output.is_enabled = False

    @log_to_debug
    def power_on(self) -> None:
        for output in self._outputs:
            if output._index == BRAIN_OUTPUT:
                continue
            output.is_enabled = True

    def __repr__(self) -> str:
        return f"<{self.__class__.__qualname__}: {self._serial}>"


class Output:
    __slots__ = ('_serial', '_index')

    def __init__(self, serial: SerialWrapper, index: int):
        self._serial = serial
        self._index = index

    @property
    @log_to_debug
    def is_enabled(self) -> bool:
        response = self._serial.query(f'OUT:{self._index}:GET?')
        return True if (response == '1') else False

    @is_enabled.setter
    @log_to_debug
    def is_enabled(self, value: bool) -> None:
        if self._index == BRAIN_OUTPUT:
            raise RuntimeError("Brain output cannot be controlled via this API.")
        if value:
            self._serial.write(f'OUT:{self._index}:SET:1')
        else:
            self._serial.write(f'OUT:{self._index}:SET:0')

    @property
    @log_to_debug
    def current(self) -> float:
        response = self._serial.query(f'OUT:{self._index}:I?')
        return float(response) / 1000

    @property
    @log_to_debug
    def overcurrent(self) -> bool:
        response = self._serial.query('*STATUS?')
        oc, *_ = response.split(':')
        port_oc = [True if (x == '1') else False for x in oc.split(',')]
        return port_oc[self._index]

    def __repr__(self) -> str:
        return f"<{self.__class__.__qualname__} index={self._index} {self._serial}>"


class Led:
    __slots__ = ('_serial', '_led')

    def __init__(self, serial: SerialWrapper, led: str):
        self._serial = serial
        self._led = led

    @log_to_debug
    def on(self) -> None:
        self._serial.write(f'LED:{self._led}:SET:1')

    @log_to_debug
    def off(self) -> None:
        self._serial.write(f'LED:{self._led}:SET:0')

    @log_to_debug
    def flash(self) -> None:
        self._serial.write(f'LED:{self._led}:SET:F')

    def __repr__(self) -> str:
        return f"<{self.__class__.__qualname__} led={self._led} {self._serial}>"


class BatterySensor:
    __slots__ = ('_serial',)

    def __init__(self, serial: SerialWrapper):
        self._serial = serial

    @property
    @log_to_debug
    def voltage(self) -> float:
        response = self._serial.query('BATT:V?')
        return float(response) / 1000

    @property
    @log_to_debug
    def current(self) -> float:
        response = self._serial.query('BATT:I?')
        return float(response) / 1000

    def __repr__(self) -> str:
        return f"<{self.__class__.__qualname__}: {self._serial}>"


class Piezo:
    __slots__ = ('_serial',)

    def __init__(self, serial: SerialWrapper):
        self._serial = serial

    @log_to_debug
    def buzz(self, duration: float, frequency: float) -> None:
        frequency_int = int(float_bounds_check(
            frequency, 8, 10_000, "Frequency is a float in Hz between 0 and 10000"))
        duration_ms = int(float_bounds_check(
            duration * 1000, 0, 2**31 - 1,
            f"Duration is a float in seconds between 0 and {(2**31-1)/1000:,.0f}"))

        cmd = f'NOTE:{frequency_int}:{duration_ms}'
        self._serial.write(cmd)

    def __repr__(self) -> str:
        return f"<{self.__class__.__qualname__}: {self._serial}>"


class Note(float, Enum):
    """An enumeration of notes.

    An enumeration of notes from scientific pitch
    notation and their related frequencies in Hz.
    """

    C6 = 1047.0
    D6 = 1174.7
    E6 = 1318.5
    F6 = 1396.9
    G6 = 1568.0
    A6 = 1760.0
    B6 = 1975.5
    C7 = 2093.0
    D7 = 2349.3
    E7 = 2637.0
    F7 = 2793.8
    G7 = 3136.0
    A7 = 3520.0
    B7 = 3951.1
    C8 = 4186.0

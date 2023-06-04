from __future__ import annotations

import logging
from enum import Enum, IntEnum

from serial.tools.list_ports import comports

from .serial_wrapper import SerialWrapper
from .utils import BoardIdentity, float_bounds_check, get_USB_identity

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


class PowerBoard:
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

        serial_identity = self.identify()
        self._serial.set_identity(serial_identity)

    @classmethod
    def _get_supported_boards(cls) -> dict[str, PowerBoard]:
        boards = {}
        serial_ports = comports()
        for port in serial_ports:
            if port.vid == 0x1BDA and port.pid == 0x0010:
                # Create board identity from USB port info
                initial_identity = get_USB_identity(port)

                try:
                    board = PowerBoard(port.device, initial_identity)
                except RuntimeError:
                    logger.warning(
                        f"Found servo board-like serial port at {port.device!r}, "
                        "but it could not be identified. Ignoring this device")
                    continue
                boards[board.identify().asset_tag] = board
        return boards

    @property
    def outputs(self) -> Outputs:
        return self._outputs

    @property
    def battery_sensor(self) -> BatterySensor:
        return self._battery_sensor

    @property
    def piezo(self) -> Piezo:
        return self._piezo

    def identify(self) -> BoardIdentity:
        response = self._serial.query('*IDN?')
        return BoardIdentity(*response.split(':'))

    @property
    def temperature(self) -> int:
        response = self._serial.query('*STATUS?')
        _, temp, _ = response.split(':')
        return int(temp)

    @property
    def fan(self) -> bool:
        response = self._serial.query('*STATUS?')
        _, _, fan = response.split(':')
        return True if (fan == '1') else False

    def reset(self) -> None:
        self._serial.write('*RESET')

    def _start_button(self) -> bool:
        response: str = self._serial.query('BTN:START:GET?')
        internal, external = response.split(':')
        return (internal == '1') or (external == '1')


class Outputs:
    def __init__(self, serial: SerialWrapper):
        self._serial = serial
        self._outputs = tuple(Output(serial, i) for i in range(7))

    def __getitem__(self, key: int) -> Output:
        return self._outputs[key]

    def power_off(self) -> None:
        for output in self._outputs:
            output.is_enabled = False

    def power_on(self) -> None:
        for output in self._outputs:
            output.is_enabled = True


class Output:
    def __init__(self, serial: SerialWrapper, index: int):
        self._serial = serial
        self._index = index

    @property
    def is_enabled(self) -> bool:
        response = self._serial.query(f'OUT:{self._index}:GET?')
        return True if (response == '1') else False

    @is_enabled.setter
    def is_enabled(self, value: bool) -> None:
        if value:
            self._serial.write(f'OUT:{self._index}:SET:1')
        else:
            self._serial.write(f'OUT:{self._index}:SET:0')

    @property
    def current(self) -> float:
        response = self._serial.query(f'OUT:{self._index}:I?')
        return float(response) / 1000

    @property
    def overcurrent(self) -> bool:
        response = self._serial.query('*STATUS?')
        oc, _, _ = response.split(':')
        port_oc = [True if (x == '1') else False for x in oc.split(',')]
        return port_oc[self._index]


class Led:
    def __init__(self, serial: SerialWrapper, led: str):
        self._serial = serial
        self.led = led

    def on(self) -> None:
        self._serial.write(f'LED:{self.led}:SET:1')

    def off(self) -> None:
        self._serial.write(f'LED:{self.led}:SET:0')

    def flash(self) -> None:
        self._serial.write(f'LED:{self.led}:SET:F')


class BatterySensor:
    def __init__(self, serial: SerialWrapper):
        self._serial = serial

    @property
    def voltage(self) -> float:
        response = self._serial.query('BATT:V?')
        return float(response) / 1000

    @property
    def current(self) -> float:
        response = self._serial.query('BATT:I?')
        return float(response) / 1000


class Piezo:
    def __init__(self, serial: SerialWrapper):
        self._serial = serial

    def buzz(self, duration: float, frequency: float) -> None:
        frequency_int = int(float_bounds_check(
            frequency, 8, 10_000, "Frequency is a float in Hz between 0 and 10000"))
        duration_ms = int(float_bounds_check(
            duration * 1000, 0, 2**31 - 1,
            f"Duration is a float in seconds between 0 and {(2**31-1)/1000:,.0f}"))

        cmd = f'NOTE:{frequency_int}:{duration_ms}'
        self._serial.write(cmd)


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

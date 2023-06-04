from __future__ import annotations

import logging

from serial.tools.list_ports import comports

from .serial_wrapper import SerialWrapper
from .utils import BoardIdentity

logger = logging.getLogger(__name__)


class PowerBoard:
    def __init__(self, serial_port: str) -> None:
        self._serial = SerialWrapper(serial_port, 115200)

        self._outputs = Outputs(self._serial)
        self._battery_sensor = BatterySensor(self._serial)
        self._piezo = Piezo(self._serial)
        self._run_led = Led(self._serial, 'RUN')
        self._error_led = Led(self._serial, 'ERR')

        self.identity = self.identify()

    @classmethod
    def _get_supported_boards(cls) -> dict[str, PowerBoard]:
        boards = {}
        serial_ports = comports()
        for port in serial_ports:
            if port.vid == 0x1BDA and port.pid == 0x0010:
                board = PowerBoard(port.device)
                boards[board.identity.asset_tag] = board
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
        response = self._serial.query('BTN:START:GET?')
        internal, external = [int(x) for x in response.split(':')]
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

    def buzz(self, duration: float, frequency: int) -> None:
        # TODO type / bounds check + add music note
        frequency_int = int(round(frequency))
        if not (0 < frequency_int < 10_000):
            raise ValueError('Frequency out of range')

        duration_ms = int(duration * 1000)

        cmd = f'NOTE:{frequency_int}:{duration_ms}'
        self._serial.write(cmd)

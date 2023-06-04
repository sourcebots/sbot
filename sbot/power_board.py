import logging

from serial.tools.list_ports import comports

from .serial_wrapper import SerialWrapper
from .utils import BoardIdentity

logger = logging.getLogger(__name__)


class PowerBoard:
    def __init__(self, serial_port):
        self._serial = SerialWrapper(serial_port, 115200)

        self._outputs = Outputs(self._serial)
        self._battery_sensor = BatterySensor(self._serial)
        self._piezo = Piezo(self._serial)
        self._run_led = Led(self._serial, 'RUN')
        self._error_led = Led(self._serial, 'ERR')

        self.identity = self.identify()

    @classmethod
    def _get_supported_boards(cls):
        boards = {}
        serial_ports = comports()
        for port in serial_ports:
            if port.vid == 0x1BDA and port.pid == 0x0010:
                board = PowerBoard(port.device)
                boards[board.identity.asset_tag] = board
        return boards

    @property
    def outputs(self):
        return self._outputs

    @property
    def battery_sensor(self):
        return self._battery_sensor

    @property
    def piezo(self):
        return self._piezo

    def identify(self):
        response = self._serial.query('*IDN?')
        return BoardIdentity(*response.split(':'))

    @property
    def temperature(self):
        response = self._serial.query('*STATUS?')
        _, temp, _ = response.split(':')
        return int(temp)

    @property
    def fan(self):
        response = self._serial.query('*STATUS?')
        _, _, fan = response.split(':')
        return (fan == '1')

    def reset(self):
        self._serial.write('*RESET')

    def start_button(self):
        _ = self._serial.query('BTN:START:GET?')
        response = self._serial.query('BTN:START:GET?')
        internal, external = [int(x) for x in response.split(':')]
        return (internal == '1') or (external == '1')


class Outputs:
    def __init__(self, serial):
        self._serial = serial
        self._outputs = tuple(Output(serial, i) for i in range(7))

    def __getitem__(self, key):
        return self._outputs[key]

    def power_off(self):
        for output in self._outputs:
            output.is_enabled = False

    def power_on(self):
        for output in self._outputs:
            output.is_enabled = True


class Output:
    def __init__(self, serial, index):
        self._serial = serial
        self._index = index

    @property
    def is_enabled(self):
        response = self._serial.query(f'OUT:{self._index}:GET?')
        return (response == '1')

    @is_enabled.setter
    def is_enabled(self, value):
        if value:
            self._serial.write(f'OUT:{self._index}:SET:1')
        else:
            self._serial.write(f'OUT:{self._index}:SET:0')

    @property
    def current(self) -> float:
        response = self._serial.query(f'OUT:{self._index}:I?')
        return float(response) / 1000

    @property
    def overcurrent(self):
        response = self._serial.query('*STATUS?')
        oc, _, _ = response.split(':')
        port_oc = [(x == '1') for x in oc.split(',')]
        return port_oc[self._index]


class Led:
    def __init__(self, serial, led):
        self._serial = serial
        self.led = led

    def on(self):
        self._serial.write(f'LED:{self.led}:SET:1')

    def off(self):
        self._serial.write(f'LED:{self.led}:SET:0')

    def flash(self):
        self._serial.write(f'LED:{self.led}:SET:F')


class BatterySensor:
    def __init__(self, serial):
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
    def __init__(self, serial):
        self._serial = serial

    def buzz(self, duration, frequency):
        # TODO type / bounds check + add music note
        frequency_int = int(round(frequency))
        if not (0 < frequency_int < 10_000):
            raise ValueError('Frequency out of range')

        duration_ms = int(duration * 1000)

        cmd = f'NOTE:{frequency_int}:{duration_ms}'
        self._serial.write(cmd)

from serial.tools.list_ports import comports

from serial_wrapper import SerialWrapper


class PowerBoard:
    def __init__(self, serial_port):
        self.serial = SerialWrapper(serial_port, 115200)

        self._outputs = Outputs(self.serial)
        self._battery_sensor = BatterySensor(self.serial)
        self._piezo = Piezo(self.serial)
        self._run_led = Led(self.serial, 'RUN')
        self._error_led = Led(self.serial, 'ERR')

    @classmethod
    def _get_supported_boards(cls):
        boards = []
        serial_ports = comports()
        for port in serial_ports:
            if port.vid == 0x1BDA and port.pid == 0x0010:
                boards.append(PowerBoard(port.device))
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
        data = self.serial.query('*IDN?')
        return data.split(':')

    @property
    def temprature(self):
        data = self.serial.query('*STATUS?')
        _, temp, _ = data.split(':')
        return int(temp)

    @property
    def fan(self):
        data = self.serial.query('*STATUS?')
        _, _, fan = data.split(':')
        return (fan == '1')

    def reset(self):
        self.serial.write('*RESET')

    def start_button(self):
        _ = self.serial.query('BTN:START:GET?')
        data = self.serial.query('BTN:START:GET?')
        internal, external = [int(x) for x in data.split(':')]
        return internal, external


class Outputs:
    def __init__(self, serial):
        self.serial = serial
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
        self.serial = serial
        self._index = index

    @property
    def is_enabled(self):
        data = self.serial.query(f'OUT:{self._index}:GET?')
        return (data == '1')

    @is_enabled.setter
    def is_enabled(self, value):
        if value:
            self.serial.write(f'OUT:{self._index}:SET:1')
        else:
            self.serial.write(f'OUT:{self._index}:SET:0')

    @property
    def current(self):
        data = self.serial.query(f'OUT:{self._index}:I?')
        return float(data)/1000

    @property
    def overcurrent(self):
        data = self.serial.query('*STATUS?')
        oc, _, _ = data.split(':')
        port_oc = [(x == '1') for x in oc.split(',')]
        return port_oc[self._index]


class Led:
    def __init__(self, serial, led):
        self.serial = serial
        self.led = led

    def on(self):
        self.serial.write(f'LED:{self.led}:SET:1')

    def off(self):
        self.serial.write(f'LED:{self.led}:SET:0')

    def flash(self):
        self.serial.write(f'LED:{self.led}:SET:F')


class BatterySensor:
    def __init__(self, serial):
        self.serial = serial

    @property
    def voltage(self):
        data = self.serial.query('BATT:V?')
        return float(data)/1000

    @property
    def current(self):
        data = self.serial.query('BATT:I?')
        return float(data)/1000


class Piezo:
    def __init__(self, serial):
        self.serial = serial

    def buzz(self, duration, frequency):
        frequency_int = int(round(frequency))
        if not (0 < frequency_int < 10_000):
            raise ValueError('Frequency out of range')

        duration_ms = int(duration * 1000)

        cmd = f'NOTE:{frequency_int}:{duration_ms}'
        self.serial.write(cmd)

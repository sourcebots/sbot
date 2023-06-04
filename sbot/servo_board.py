import logging

from serial.tools.list_ports import comports

from .serial_wrapper import SerialWrapper
from .utils import BoardIdentity, map_to_float, map_to_int

DUTY_MIN = 500
DUTY_MAX = 4000
START_DUTY_MIN = 1000
START_DUTY_MAX = 2000

logger = logging.getLogger(__name__)


class ServoBoard:
    def __init__(self, serial_port):
        self._serial = SerialWrapper(serial_port, 115200)

        self._servos = tuple(
            Servo(self._serial, index) for index in range(12)
        )

        self.identity = self.identify()

    @classmethod
    def _get_supported_boards(cls):
        boards = {}
        serial_ports = comports()
        for port in serial_ports:
            if port.vid == 0x1BDA and port.pid == 0x0011:
                board = ServoBoard(port.device)
                boards[board.identity.asset_tag] = board
        return boards

    @property
    def servos(self):
        return self._servos

    def identify(self):
        response = self._serial.query('*IDN?')
        return BoardIdentity(*response.split(':'))

    def status(self):
        response = self._serial.query('*STATUS?')

        data = response.split(':')
        watchdog_fail = (data[0] == '1')
        pgood = (data[1] == '1')

        return watchdog_fail, pgood

    def reset(self):
        self._serial.write('*RESET')

    @property
    def current(self):
        response = self._serial.query('SERVO:I?')
        return float(response) / 1000

    @property
    def voltage(self):
        response = self._serial.query('SERVO:V?')
        return float(response) / 1000


class Servo:
    def __init__(self, serial, index):
        self._serial = serial
        self._index = index

        self._duty_min = START_DUTY_MIN
        self._duty_max = START_DUTY_MAX

    def set_duty_limits(self, lower, upper):
        if not (isinstance(lower, int) and isinstance(upper, int)):
            raise TypeError(
                f'Servo pulse limits are ints in µs, in the range {DUTY_MIN} to {DUTY_MAX}'
            )
        if not (DUTY_MIN <= lower <= DUTY_MAX and DUTY_MIN <= upper <= DUTY_MAX):
            raise ValueError(
                f'Servo pulse limits are ints in µs, in the range {DUTY_MIN} to {DUTY_MAX}'
            )

        self._duty_min = lower
        self._duty_max = upper

    def get_duty_limits(self):
        return self._duty_min, self._duty_max

    @property
    def position(self):
        response = self._serial.query(f'SERVO:{self._index}:GET?')
        data = int(response)
        if data == 0:
            return None
        return map_to_float(data, self._duty_min, self._duty_max, -1.0, 1.0, precision=3)

    @position.setter
    def position(self, value):
        try:
            if (value < -1.0) or (value > 1.0):
                raise ValueError('Servo position is a float between -1.0 and 1.0')
        except TypeError:
            raise TypeError('Servo position is a float between -1.0 and 1.0')

        setpoint = map_to_int(value, -1.0, 1.0, self._duty_min, self._duty_max)
        self._serial.write(f'SERVO:{self._index}:SET:{setpoint}')

    def disable(self):
        self._serial.write(f'SERVO:{self._index}:DISABLE')


if __name__ == '__main__':
    servoboards = ServoBoard._get_supported_boards()
    for s in servoboards:
        print(s.identify())

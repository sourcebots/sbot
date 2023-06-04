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
        self.serial = SerialWrapper(serial_port, 115200)

        self._servos = tuple(
            Servo(self.serial, index) for index in range(12)
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
        data = self.serial.query('*IDN?')
        return BoardIdentity(*data.split(':'))

    def status(self):
        data = self.serial.query('*STATUS?')
        return data

    def reset(self):
        self.serial.write('*RESET')

    @property
    def current(self):
        return self.serial.query('SERVO:I?')

    @property
    def voltage(self):
        return self.serial.query('SERVO:V?')


class Servo:
    def __init__(self, serial, index):
        self._serial = serial
        self._index = index

        self._duty_min = START_DUTY_MIN
        self._duty_max = START_DUTY_MAX

    def set_duty_limits(self, lower, upper):
        # TODO check int provided
        # TODO check int falls in the correct bounds
        self._duty_min = lower
        self._duty_max = upper

    def get_duty_limits(self):
        return self._duty_min, self._duty_max

    @property
    def position(self):
        value = self._serial.query(f'SERVO:{self._index}:GET?')
        if value == 0:
            return None
        return map_to_float(value, self._duty_min, self._duty_max, -1.0, 1.0, precision=3)

    @position.setter
    def position(self, value):
        setpoint = map_to_int(value, -1.0, 1.0, self._duty_min, self._duty_max)
        self._serial.write(f'SERVO:{self._index}:SET:{setpoint}')

    def disable(self):
        self._serial.write(f'SERVO:{self._index}:DISABLE')


if __name__ == '__main__':
    servoboards = ServoBoard._get_supported_boards()
    for s in servoboards:
        print(s.identify())

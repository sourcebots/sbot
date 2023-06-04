import logging
from enum import Enum

from serial.tools.list_ports import comports

from .serial_wrapper import SerialWrapper
from .utils import BoardIdentity, map_to_float, map_to_int

logger = logging.getLogger(__name__)


class MotorSpecialState(Enum):
    """An enum of the special states that a motor can be set to."""
    BRAKE = 0
    COAST = 1


class MotorBoard:
    def __init__(self, serial_port):
        self._serial = SerialWrapper(serial_port, 115200)

        self._motors = (
            Motor(self._serial, 0),
            Motor(self._serial, 1)
        )

        self.identity = self.identify()

    @classmethod
    def _get_supported_boards(cls):
        boards = {}
        serial_ports = comports()
        for port in serial_ports:
            if port.vid == 0x0403 and port.pid == 0x6001:
                board = MotorBoard(port.device)
                boards[board.identity.asset_tag] = board
        return boards

    @property
    def motors(self):
        return self._motors

    def identify(self):
        response = self._serial.query('*IDN?')
        return BoardIdentity(*response.split(':'))

    def status(self):
        response = self._serial.query('*STATUS?')

        data = response.split(':')
        output_faults = [(port == '1') for port in data[0].split(',')]
        input_voltage = float(data[1]) / 1000

        return output_faults, input_voltage

    def reset(self):
        self._serial.write('*RESET')


class Motor:
    def __init__(self, serial, index):
        self._serial = serial
        self._index = index

    @property
    def power(self):
        response = self._serial.query(f'MOT:{self._index}:GET?')

        data = response.split(':')
        enabled = (data[0] == '1')
        value = int(data[1])

        if not enabled:
            return MotorSpecialState.COAST
        return map_to_float(value, -1000, 1000, -1.0, 1.0, precision=3)

    @power.setter
    def power(self, value):
        try:
            if (value < -1.0) or (value > 1.0):
                raise ValueError('Motor power is a float between -1.0 and 1.0')
        except TypeError:
            raise TypeError('Motor power is a float between -1.0 and 1.0')

        if value == MotorSpecialState.COAST:
            self._serial.write(f'MOT:{self._index}:DISABLE')
        elif value == MotorSpecialState.BRAKE:
            self._serial.write(f'MOT:{self._index}:SET:0')
        else:
            setpoint = map_to_int(value, -1.0, 1.0, -1000, 1000)
            self._serial.write(f'MOT:{self._index}:SET:{setpoint}')

    @property
    def current(self):
        response = self._serial.query(f'MOT:{self._index}:I?')
        return float(response) / 1000


if __name__ == '__main__':
    motorboards = MotorBoard._get_supported_boards()
    for m in motorboards:
        print(m.identify())

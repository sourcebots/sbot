from enum import Enum

from serial.tools.list_ports import comports

from .serial_wrapper import SerialWrapper
from .utils import map_to_float, map_to_int


class MotorSpecialState(Enum):
    """An enum of the special states that a motor can be set to."""
    BRAKE = 0
    COAST = 1


class MotorBoard:
    def __init__(self, serial_port):
        self.serial = SerialWrapper(serial_port, 115200)

        self._motors = (
            Motor(self.serial, 0),
            Motor(self.serial, 1)
        )

    @classmethod
    def _get_supported_boards(cls):
        boards = []
        serial_ports = comports()
        for port in serial_ports:
            if port.vid == 0x0403 and port.pid == 0x6001:
                boards.append(MotorBoard(port.device))
        return boards

    @property
    def motors(self):
        return self._motors

    def identify(self):
        data = self.serial.query('*IDN?')
        return data.split(':')

    def status(self):
        data = self.serial.query('*STATUS?')
        return data

    def reset(self):
        self.serial.write('*RESET')


class Motor:
    def __init__(self, serial, index):
        self._serial = serial
        self._index = index

    @property
    def power(self):
        data = self.serial.query(f'MOT:{self._index}:GET?')
        enabled, value = data.split(':')
        if enabled == '0':
            return MotorSpecialState.COAST
        return map_to_float(value, -1000, 1000, -1.0, 1.0, precision=3)

    @power.setter
    def power(self, value):
        # TODO rescale -1.1 -> -127.127
        if value == MotorSpecialState.COAST:
            self.serial.write(f'MOT:{self._index}:DISABLE')
        elif value == MotorSpecialState.BRAKE:
            self.serial.write(f'MOT:{self._index}:SET:0')
        else:
            setpoint = map_to_int(value, -1.0, 1.0, -1000, 1000)
            self.serial.write(f'MOT:{self._index}:SET:{setpoint}')

    @property
    def current(self):
        return self.serial.query(f'MOT:{self._index}:I?')


if __name__ == '__main__':
    motorboards = MotorBoard._get_supported_boards()
    for m in motorboards:
        print(m.identify())

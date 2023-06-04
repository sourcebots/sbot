from __future__ import annotations

import logging

from serial.tools.list_ports import comports

from .serial_wrapper import SerialWrapper
from .utils import BoardIdentity, float_bounds_check, map_to_float, map_to_int

logger = logging.getLogger(__name__)

BRAKE = 0
COAST = float("-inf")


class MotorBoard:
    def __init__(self, serial_port: str) -> None:
        self._serial = SerialWrapper(serial_port, 115200)

        self._motors = (
            Motor(self._serial, 0),
            Motor(self._serial, 1)
        )

        self.identity = self.identify()

    @classmethod
    def _get_supported_boards(cls) -> dict[str, MotorBoard]:
        boards = {}
        serial_ports = comports()
        for port in serial_ports:
            if port.vid == 0x0403 and port.pid == 0x6001:
                # TODO handle identity failing
                board = MotorBoard(port.device)
                boards[board.identity.asset_tag] = board
        return boards

    @property
    def motors(self) -> tuple[Motor, Motor]:
        return self._motors

    def identify(self) -> BoardIdentity:
        response = self._serial.query('*IDN?')
        return BoardIdentity(*response.split(':'))

    def status(self) -> tuple[list[bool], float]:
        response = self._serial.query('*STATUS?')

        data = response.split(':')
        output_faults = [True if (port == '1') else False for port in data[0].split(',')]
        input_voltage = float(data[1]) / 1000

        return output_faults, input_voltage

    def reset(self) -> None:
        self._serial.write('*RESET')


class Motor:
    def __init__(self, serial: SerialWrapper, index: int):
        self._serial = serial
        self._index = index

    @property
    def power(self) -> float:
        response = self._serial.query(f'MOT:{self._index}:GET?')

        data = response.split(':')
        enabled = (data[0] == '1')
        value = int(data[1])

        if not enabled:
            return COAST
        return map_to_float(value, -1000, 1000, -1.0, 1.0, precision=3)

    @power.setter
    def power(self, value: float) -> None:
        if value == COAST:
            self._serial.write(f'MOT:{self._index}:DISABLE')
            return
        value = float_bounds_check(
            value, -1.0, 1.0,
            'Motor power is a float between -1.0 and 1.0')

        if value == BRAKE:
            self._serial.write(f'MOT:{self._index}:SET:0')
        else:
            setpoint = map_to_int(value, -1.0, 1.0, -1000, 1000)
            self._serial.write(f'MOT:{self._index}:SET:{setpoint}')

    @property
    def current(self) -> float:
        response = self._serial.query(f'MOT:{self._index}:I?')
        return float(response) / 1000


if __name__ == '__main__':
    motorboards = MotorBoard._get_supported_boards()
    for serial_num, board in motorboards.items():
        print(serial_num)
        print(board.identify())

from __future__ import annotations

import logging

from serial.tools.list_ports import comports

from .serial_wrapper import SerialWrapper
from .utils import (
    BoardIdentity, float_bounds_check,
    get_USB_identity, map_to_float, map_to_int,
)

DUTY_MIN = 500
DUTY_MAX = 4000
START_DUTY_MIN = 1000
START_DUTY_MAX = 2000

logger = logging.getLogger(__name__)


class ServoBoard:
    def __init__(
        self,
        serial_port: str,
        initial_identity: BoardIdentity | None = None,
    ) -> None:
        if initial_identity is None:
            initial_identity = BoardIdentity()
        self._serial = SerialWrapper(serial_port, 115200, identity=initial_identity)

        self._servos = tuple(
            Servo(self._serial, index) for index in range(12)
        )

        serial_identity = self.identify()
        self._serial.set_identity(serial_identity)

    @classmethod
    def _get_supported_boards(cls) -> dict[str, 'ServoBoard']:
        boards = {}
        serial_ports = comports()
        for port in serial_ports:
            if port.vid == 0x1BDA and port.pid == 0x0011:
                # Create board identity from USB port info
                initial_identity = get_USB_identity(port)

                try:
                    board = ServoBoard(port.device, initial_identity)
                except RuntimeError:
                    logger.warning(
                        f"Found servo board-like serial port at {port.device!r}, "
                        "but it could not be identified. Ignoring this device")
                    continue
                boards[board.identify().asset_tag] = board
        return boards

    @property
    def servos(self) -> tuple['Servo', ...]:
        return self._servos

    def identify(self) -> BoardIdentity:
        response = self._serial.query('*IDN?')
        return BoardIdentity(*response.split(':'))

    def status(self) -> tuple[bool, bool]:
        response = self._serial.query('*STATUS?')

        data = response.split(':')
        watchdog_fail = (data[0] == '1')
        pgood = (data[1] == '1')

        return watchdog_fail, pgood

    def reset(self) -> None:
        self._serial.write('*RESET')

    @property
    def current(self) -> float:
        response = self._serial.query('SERVO:I?')
        return float(response) / 1000

    @property
    def voltage(self) -> float:
        response = self._serial.query('SERVO:V?')
        return float(response) / 1000


class Servo:
    def __init__(self, serial: SerialWrapper, index: int):
        self._serial = serial
        self._index = index

        self._duty_min = START_DUTY_MIN
        self._duty_max = START_DUTY_MAX

    def set_duty_limits(self, lower: int, upper: int) -> None:
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

    def get_duty_limits(self) -> tuple[int, int]:
        return self._duty_min, self._duty_max

    @property
    def position(self) -> float | None:
        response = self._serial.query(f'SERVO:{self._index}:GET?')
        data = int(response)
        if data == 0:
            return None
        return map_to_float(data, self._duty_min, self._duty_max, -1.0, 1.0, precision=3)

    @position.setter
    def position(self, value: float | None) -> None:
        if value is None:
            self.disable()
            return
        value = float_bounds_check(
            value, -1.0, 1.0,
            'Servo position is a float between -1.0 and 1.0')

        setpoint = map_to_int(value, -1.0, 1.0, self._duty_min, self._duty_max)
        self._serial.write(f'SERVO:{self._index}:SET:{setpoint}')

    def disable(self) -> None:
        self._serial.write(f'SERVO:{self._index}:DISABLE')


if __name__ == '__main__':
    servoboards = ServoBoard._get_supported_boards()
    for serial_num, board in servoboards.items():
        print(serial_num)
        print(board.identify())

from __future__ import annotations

import atexit
import logging

from serial.tools.list_ports import comports

from .serial_wrapper import SerialWrapper
from .utils import (
    BoardIdentity, float_bounds_check,
    get_USB_identity, map_to_float, map_to_int,
)

logger = logging.getLogger(__name__)

BRAKE = 0
COAST = float("-inf")


class MotorBoard:
    def __init__(
        self,
        serial_port: str,
        initial_identity: BoardIdentity | None = None,
    ) -> None:
        if initial_identity is None:
            initial_identity = BoardIdentity()
        self._serial = SerialWrapper(serial_port, 115200, identity=initial_identity)

        self._motors = (
            Motor(self._serial, 0),
            Motor(self._serial, 1)
        )

        serial_identity = self.identify()
        self._serial.set_identity(serial_identity)

        atexit.register(self._cleanup, serial_num=serial_identity.asset_tag)

    @classmethod
    def _get_supported_boards(cls) -> dict[str, MotorBoard]:
        boards = {}
        serial_ports = comports()
        for port in serial_ports:
            if port.vid == 0x0403 and port.pid == 0x6001:
                # Create board identity from USB port info
                initial_identity = get_USB_identity(port)

                try:
                    board = MotorBoard(port.device, initial_identity)
                except RuntimeError:
                    logger.warning(
                        f"Found motor board-like serial port at {port.device!r}, "
                        "but it could not be identified. Ignoring this device")
                    continue
                boards[board.identify().asset_tag] = board
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

    def _cleanup(self, serial_num: str) -> None:
        try:
            self.reset()
        except Exception:
            logger.warning(f"Failed to cleanup motor board {serial_num}.")


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

from __future__ import annotations

import logging
import sys
import threading
import time
from collections.abc import Callable
from functools import wraps
from typing import TypeVar

import serial

from .logging import TRACE
from .utils import BoardIdentity

logger = logging.getLogger(__name__)

if sys.version_info < (3, 10):
    from typing_extensions import ParamSpec
else:
    from typing import ParamSpec
Param = ParamSpec("Param")
RetType = TypeVar("RetType")

Func = Callable[Param, RetType]
E = TypeVar("E", bound=BaseException)


def retry(times: int, exceptions: type[E]) -> Callable[[Func], Func]:
    def decorator(func: Callable[Param, RetType]) -> Callable[Param, RetType]:
        @wraps(func)
        def retryfn(*args: Param.args, **kwargs: Param.kwargs) -> RetType:
            attempt = 0
            while attempt < times:
                try:
                    return func(*args, **kwargs)
                except exceptions:
                    attempt += 1
            return func(*args, **kwargs)
        return retryfn
    return decorator

# TODO error handling and log messages


class SerialWrapper:
    def __init__(
        self,
        port: str,
        baud: int,
        timeout: float = 0.5,
        identity: BoardIdentity = BoardIdentity(),
        delay_after_connect: float = 0,
    ):
        self._lock = threading.Lock()
        self.identity = identity

        # Serial port parameters
        self.port = port
        self.baud = baud
        self.timeout = timeout

        self.delay_after_connect = delay_after_connect

        # pyserial serial port
        self.serial: serial.Serial | None = None

        # Current port state
        self.connected = False

    def start(self) -> None:
        self._connect()

    def stop(self) -> None:
        self._disconnect()

    @retry(times=3, exceptions=RuntimeError)
    def query(self, data: str) -> str:
        with self._lock:
            if not self.connected:
                if not self._connect():
                    print('Error')
                    raise RuntimeError('Board not connected')

            if self.serial is None:
                raise RuntimeError('Serial port is None')

            try:
                logger.log(TRACE, f'Serial write - "{data}"')
                cmd = data + '\n'
                self.serial.write(cmd.encode())

                response = self.serial.readline()
                logger.log(TRACE, f'Serial read  - "{response.decode().strip()}"')

                if b'\n' not in response:
                    raise serial.SerialException('readline timeout')
            except serial.SerialException:
                # Serial port was closed
                # Make sure port is cleaned up
                self._disconnect()
                raise RuntimeError('Board disconnected')

            return response.decode().strip()

    def write(self, data: str) -> None:
        response = self.query(data)
        if 'NACK' in response:
            _, error_msg = response.split(':', maxsplit=1)
            raise RuntimeError(error_msg)

    def _connect(self) -> bool:
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baud,
                timeout=self.timeout
            )
            self.connected = True
            time.sleep(self.delay_after_connect)
        except serial.SerialException:
            return False

        logger.info('Connected')
        return True

    def _disconnect(self) -> None:
        if self.serial is not None:
            logger.info('Disconnected')
            self.connected = False
            self.serial.close()
            self.serial = None

    def set_identity(self, identity: BoardIdentity) -> None:
        self.identity = identity

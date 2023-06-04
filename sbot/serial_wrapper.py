from __future__ import annotations

import logging
import sys
import threading
import time
from collections.abc import Callable
from functools import wraps
from typing import TypeVar

import serial

from .exceptions import BoardDisconnectionError
from .logging import TRACE
from .utils import BoardIdentity

logger = logging.getLogger(__name__)

if sys.version_info < (3, 10):
    from typing_extensions import ParamSpec
else:
    from typing import ParamSpec
Param = ParamSpec("Param")
RetType = TypeVar("RetType")

E = TypeVar("E", bound=BaseException)


def retry(
        times: int, exceptions: type[E],
) -> Callable[[Callable[Param, RetType]], Callable[Param, RetType]]:
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

    @retry(times=3, exceptions=BoardDisconnectionError)
    def query(self, data: str) -> str:
        with self._lock:
            if not self.connected:
                if not self._connect():
                    raise BoardDisconnectionError(
                        'Connection to board could not be established',
                        board=self.identity,
                    )

            if self.serial is None:
                raise RuntimeError('Serial port is None')

            try:
                logger.log(TRACE, f'Serial write - "{data}"')
                cmd = data + '\n'
                self.serial.write(cmd.encode())

                response = self.serial.readline()
                logger.log(TRACE, f'Serial read  - "{response.decode().strip()}"')

                if b'\n' not in response:
                    # If readline times out no error is raised it returns an incomplete string
                    logger.warning((
                        f'Connection to board {self.identity.board_type}:'
                        f'{self.identity.asset_tag} timed out waiting for response'
                    ))
                    raise serial.SerialException('Timeout on readline')
            except serial.SerialException:
                # Serial port was closed
                # Make sure port is cleaned up
                self._disconnect()
                raise BoardDisconnectionError(
                    'Board disconnected during transaction',
                    board=self.identity,
                )

            return response.decode().strip()

    def write(self, data: str) -> None:
        response = self.query(data)
        if 'NACK' in response:
            _, error_msg = response.split(':', maxsplit=1)
            logger.error((
                f'Board {self.identity.board_type}:{self.identity.asset_tag} '
                f'returned NACK on write command: {error_msg}'
            ))
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
            logger.error((
                'Failed to connect to board '
                f'{self.identity.board_type}:{self.identity.asset_tag}'
            ))
            return False

        logger.info(
            f'Connected to board {self.identity.board_type}:{self.identity.asset_tag}'
        )
        return True

    def _disconnect(self) -> None:
        if self.serial is not None:
            logger.warning(
                f'Board {self.identity.board_type}:{self.identity.asset_tag} disconnected'
            )
            self.connected = False
            self.serial.close()
            self.serial = None

    def set_identity(self, identity: BoardIdentity) -> None:
        self.identity = identity

    def __str__(self) -> str:
        return f"<{self.__class__.__qualname__} {self.port!r} {self.identity.asset_tag!r}>"

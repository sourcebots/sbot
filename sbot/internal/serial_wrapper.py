"""
SerialWrapper class for communicating with boards over serial.

This class is responsible for opening and closing the serial port,
and for handling port timeouts and disconnections.
"""
from __future__ import annotations

import logging
import sys
import threading
import time
from functools import wraps
from typing import Callable, TypeVar

import serial

from .exceptions import BoardDisconnectionError
from .logging import TRACE
from .utils import IN_SIMULATOR, BoardIdentity

logger = logging.getLogger(__name__)

if sys.version_info < (3, 10):
    from typing_extensions import ParamSpec
else:
    from typing import ParamSpec
Param = ParamSpec("Param")
RetType = TypeVar("RetType")

E = TypeVar("E", bound=BaseException)
BASE_TIMEOUT: float | None

if IN_SIMULATOR:
    BASE_TIMEOUT = None  # Disable timeouts while in the simulator to allow for pausing
else:
    BASE_TIMEOUT = 0.5


def retry(
    times: int, exceptions: type[E] | tuple[type[E], ...]
) -> Callable[[Callable[Param, RetType]], Callable[Param, RetType]]:
    """
    Decorator to retry a function a number of times on a given exception.

    If the function fails on the last attempt the exception is raised.
    This outer function is used to pass arguments to the decorator.

    :param times: The number of times to retry the function.
    :param exceptions: The exception to catch and retry on.
    :return: The templated decorator function.
    """
    def decorator(func: Callable[Param, RetType]) -> Callable[Param, RetType]:
        """
        The actual decorator function that is returned by the decorator.

        The decorator retries the function a number of times on a given exception.
        If the function fails on the last attempt the exception is raised.

        :param func: The function to decorate.
        :return: The decorated function.
        """
        @wraps(func)
        def retryfn(*args: Param.args, **kwargs: Param.kwargs) -> RetType:
            """
            The function that wraps the original function.

            This function retries the original function a number of times on a given exception.

            :return: The return value of the original function.
            """
            attempt = 0
            while attempt < times:
                try:
                    return func(*args, **kwargs)
                except exceptions:
                    time.sleep(attempt * 0.5)
                    attempt += 1
            return func(*args, **kwargs)
        return retryfn
    return decorator


class SerialWrapper:
    """
    Wrapper class for serial communication with boards.

    This class is responsible for opening and closing the serial port,
    and for handling port timeouts and disconnections.

    :param port: The serial port to connect to.
    :param baud: The baud rate to use for the serial connection.
    :param timeout: The timeout for the serial connection.
    :param identity: The identity of the board this serial wrapper is connected to.
    :param delay_after_connect: The time to wait after connecting to the board before sending
                                data.
    """

    def __init__(
        self,
        port: str,
        baud: int,
        timeout: float | None = BASE_TIMEOUT,
        identity: BoardIdentity = BoardIdentity(),
        delay_after_connect: float = 0,
    ):
        # Mutex serial port access to allow for multiple threads to use the same serial port
        self._lock = threading.Lock()
        self.identity = identity

        # Time to wait before sending data after connecting to a board
        self.delay_after_connect = delay_after_connect

        # pyserial serial port, the port will be opened on the first message
        self.serial = serial.serial_for_url(
            port,
            baudrate=baud,
            timeout=timeout,
            write_timeout=timeout,
            do_not_open=True,
        )

    def start(self) -> None:
        """
        Helper method to open the serial port.

        This is not usually needed as the port will be opened on the first message.
        """
        self._connect()

    def stop(self) -> None:
        """
        Helper method to close the serial port.

        This is not usually needed as the port will be closed on garbage collection.
        """
        self._disconnect()

    @retry(times=3, exceptions=(BoardDisconnectionError, UnicodeDecodeError))
    def query(self, data: str) -> str:
        """
        Send a command to the board and return the response.

        This method will automatically reconnect to the board and retry the command
        up to 3 times on serial errors.

        :param data: The data to write to the board.
        :raises BoardDisconnectionError: If the serial connection fails during the transaction,
            including failing to respond to the command.
        :return: The response from the board with the trailing newline removed.
        """
        with self._lock:
            if not self.serial.is_open:
                if not self._connect():
                    # If the serial port cannot be opened raise an error,
                    # this will be caught by the retry decorator
                    raise BoardDisconnectionError((
                        f'Connection to board {self.identity.board_type}:'
                        f'{self.identity.asset_tag} could not be established',
                    ))

            try:
                logger.log(TRACE, f'Serial write - {data!r}')
                cmd = data + '\n'
                self.serial.write(cmd.encode())

                response = self.serial.readline()
                try:
                    response_str = response.decode().rstrip('\n')
                except UnicodeDecodeError as e:
                    logger.warning(
                        f"Board {self.identity.board_type}:{self.identity.asset_tag} "
                        f"returned invalid characters: {response!r}")
                    raise e
                logger.log(
                    TRACE, f'Serial read  - {response_str!r}')

                if b'\n' not in response:
                    # If readline times out no error is raised, it returns an incomplete string
                    logger.warning((
                        f'Connection to board {self.identity.board_type}:'
                        f'{self.identity.asset_tag} timed out waiting for response'
                    ))
                    raise serial.SerialException('Timeout on readline')
            except serial.SerialException:
                # Serial connection failed, close the port and raise an error
                self._disconnect()
                raise BoardDisconnectionError((
                    f'Board {self.identity.board_type}:{self.identity.asset_tag} '
                    'disconnected during transaction'
                ))

            if response_str.startswith('NACK'):
                _, error_msg = response_str.split(':', maxsplit=1)
                logger.error((
                    f'Board {self.identity.board_type}:{self.identity.asset_tag} '
                    f'returned NACK on write command: {error_msg}'
                ))
                raise RuntimeError(error_msg)

            return response_str

    def write(self, data: str) -> None:
        """
        Send a command to the board that does not require a response.

        :param data: The data to write to the board.
        :raises RuntimeError: If the board returns a NACK response,
            the firmware's error message is raised.
        """
        _ = self.query(data)

    def _connect(self) -> bool:
        """
        Connect to the class's serial port.

        This is called automatically when a message is sent to the board or the
        serial connection is lost.

        :raises serial.SerialException: If the serial port cannot be opened.
        :return: True if the serial port was opened successfully, False otherwise.
        """
        try:
            self.serial.open()
            if not IN_SIMULATOR:
                # Wait for the board to be ready to receive data
                # Certain boards will reset when the serial port is opened
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
        """
        Close the class's serial port.

        This is called automatically when the serial connection fails.
        The serial port will be reopened on the next message.
        """
        self.serial.close()
        logger.warning(
            f'Board {self.identity.board_type}:{self.identity.asset_tag} disconnected'
        )

    def set_identity(self, identity: BoardIdentity) -> None:
        """
        Stores the identity of the board this serial wrapper is connected to.

        This is used for logging purposes.

        :param identity: The identity of the board this serial wrapper is connected to.
        """
        self.identity = identity

    def __str__(self) -> str:
        return (
            f"<{self.__class__.__qualname__} {self.serial.port!r} {self.identity.asset_tag!r}>"
        )

    def __lt__(self, other: SerialWrapper) -> bool:
        return self.identity.asset_tag.lower() < other.identity.asset_tag.lower()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SerialWrapper):
            return False
        if self.identity.asset_tag != "":
            return self.identity.asset_tag == other.identity.asset_tag
        else:
            return self.serial.port == other.serial.port

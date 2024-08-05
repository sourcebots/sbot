"""
SerialWrapper class for communicating with boards over serial.

This class is responsible for opening and closing the serial port,
and for handling port timeouts and disconnections.
"""
from __future__ import annotations

import itertools
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
        This is the actual decorator function that is returned by the decorator.

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

    def _connect_if_needed(self) -> None:
        if not self.serial.is_open:
            if not self._connect():
                # If the serial port cannot be opened raise an error,
                # this will be caught by the retry decorator
                raise BoardDisconnectionError((
                    f'Connection to board {self.identity.board_type}:'
                    f'{self.identity.asset_tag} could not be established',
                ))

    @retry(times=3, exceptions=(BoardDisconnectionError, UnicodeDecodeError))
    def query_multi(self, commands: list[str]) -> list[str]:
        """
        Send a command to the board and return the response.

        This method will automatically reconnect to the board and retry the commands
        up to 3 times on serial errors.

        :param commands: The commands to write to the board.
        :raises BoardDisconnectionError: If the serial connection fails during the transaction,
            including failing to respond to the command.
        :return: The responses from the board with the trailing newlines removed.
        """
        # Verify no command has a newline in it, and build a command `bytes` from the
        # list of commands
        encoded_commands: list[bytes] = []
        invalid_commands: list[tuple[str, str]] = []

        for command in commands:
            if '\n' in command:
                invalid_commands.append(("contains newline", command))
            else:
                try:
                    byte_form = command.encode(encoding='utf-8')
                except UnicodeEncodeError as e:
                    invalid_commands.append((str(e), command))
                else:
                    encoded_commands.append(byte_form)
                    encoded_commands.append(b'\n')

        if invalid_commands:
            invalid_commands.sort()

            invalid_command_groups = dict(itertools.groupby(
                invalid_commands,
                key=lambda x: x[0],
            ))

            error_message = "\n".join(
                ["Invalid commands:"] +
                [
                    f"  {reason}: " + ", ".join(
                        repr(command)
                        for _, command in grouped_commands
                    )
                    for reason, grouped_commands in invalid_command_groups.items()
                ],
            )
            raise ValueError(error_message)

        full_commands = b''.join(encoded_commands)

        with self._lock:
            # If the serial port is not open, try to connect
            self._connect_if_needed()  # TODO: Write me

            # Contain all the serial IO in a try-catch; on error, disconnect and raise an error
            try:
                # Send the commands to the board
                self.serial.write(full_commands)

                # Log the commands
                for command in commands:
                    logger.log(TRACE, f"Serial write - {command!r}")

                # Read as many lines as there are commands
                responses_binary = [
                    self.serial.readline()
                    for _ in range(len(commands))
                ]

                # Log the responses. For backwards compatibility reasons, we decode
                # these separately here before any error processing, so that the
                # logs are correct even if an error occurs.
                for response_binary in responses_binary:
                    response_decoded = response_binary.decode(
                        "utf-8",
                        errors="replace",
                    ).rstrip('\n')
                    logger.log(TRACE, f"Serial read  - {response_decoded!r}")

                # Check all responses have a trailing newline (an incomplete
                # response will not).
                # This is within the lock and try-catch to ensure the serial port
                # is closed on error.
                if not all(response.endswith(b'\n') for response in responses_binary):
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

        # Decode all the responses as UTF-8
        try:
            responses_decoded = [
                response.decode("utf-8").rstrip('\n')
                for response in responses_binary
            ]
        except UnicodeDecodeError as e:
            logger.warning(
                f"Board {self.identity.board_type}:{self.identity.asset_tag} "
                f"returned invalid characters: {responses_binary!r}")
            raise e

        # Collect any NACK responses; if any, raise an error
        nack_prefix = 'NACK:'
        nack_responses = [
            response
            for response in responses_decoded
            if response.startswith(nack_prefix)
        ]

        if nack_responses:
            errors = [response[len(nack_prefix):] for response in nack_responses]
            # We can't use exception groups due to needing to support Python 3.8
            raise (
                RuntimeError(errors[0])
                if len(errors) == 1
                else RuntimeError("Multiple errors: " + ", ".join(errors))
            )

        # Return the list of responses
        return responses_decoded

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
        return self.query_multi([data])[0]

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

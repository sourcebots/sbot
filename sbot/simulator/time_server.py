"""A virtual clock source connected over a socket connection."""

from __future__ import annotations

import logging
from datetime import datetime

from ..internal.exceptions import BoardDisconnectionError, IncorrectBoardError
from ..internal.serial_wrapper import SerialWrapper
from ..internal.utils import BoardIdentity, get_simulator_boards

logger = logging.getLogger(__name__)

BAUDRATE = 115200


class TimeServer:
    """
    A virtual clock source connected over a socket connection.

    :param serial_port: The URL of the serial port to connect to.
    """

    @staticmethod
    def get_board_type() -> str:
        """
        Return the type of the board.

        :return: The literal string 'TimeServer'.
        """
        return 'TimeServer'

    def __init__(
        self,
        serial_port: str,
        initial_identity: BoardIdentity | None = None,
    ) -> None:
        if initial_identity is None:
            initial_identity = BoardIdentity()
        self._serial = SerialWrapper(
            serial_port,
            BAUDRATE,
            identity=initial_identity,
            # Disable the timeout so sleep works properly
            timeout=None,
        )

        self._identity = self.identify()
        if self._identity.board_type != self.get_board_type():
            raise IncorrectBoardError(self._identity.board_type, self.get_board_type())
        self._serial.set_identity(self._identity)

    @classmethod
    def initialise(cls) -> 'TimeServer' | None:
        """
        Initialise the board.

        :return: The initialised board, or None if no board is found.
        """
        # The filter here is the name of the emulated board in the simulator
        boards = get_simulator_boards('TimeServer')

        if not boards:
            return None

        board_info = boards[0]

        # Create board identity from the info given
        initial_identity = BoardIdentity(
            manufacturer='sbot_simulator',
            board_type=board_info.type_str,
            asset_tag=board_info.serial_number,
        )

        try:
            board = cls(board_info.url, initial_identity)
        except BoardDisconnectionError:
            logger.warning(
                f"Simulator specified time server at port {board_info.url!r}, "
                "could not be identified. Ignoring this device")
            return None
        except IncorrectBoardError as err:
            logger.warning(
                f"Board returned type {err.returned_type!r}, "
                f"expected {err.expected_type!r}. Ignoring this device")
            return None

        return board

    def identify(self) -> BoardIdentity:
        """
        Get the identity of the board.

        :return: The identity of the board.
        """
        response = self._serial.query('*IDN?')
        return BoardIdentity(*response.split(':'))

    def get_time(self) -> float:
        """
        Get the current time from the board.

        :return: The current time in seconds since the epoch.
        """
        time_str = self._serial.query('TIME?')
        return datetime.fromisoformat(time_str).timestamp()

    def sleep(self, duration: float) -> None:
        """
        Sleep for a specified duration.

        :param duration: The duration to sleep for in seconds.
        """
        if duration < 0:
            raise ValueError("sleep length must be non-negative")

        self._serial.query(f'SLEEP:{int(duration * 1000)}')

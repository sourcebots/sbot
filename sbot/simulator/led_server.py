"""Interface to control user LEDs over a socket."""
from __future__ import annotations

import logging

from ..internal.exceptions import BoardDisconnectionError, IncorrectBoardError
from ..internal.serial_wrapper import SerialWrapper
from ..internal.utils import Board, BoardIdentity, get_simulator_boards

logger = logging.getLogger(__name__)

# This value is not actually used since the serial port is a TCP socket
BAUDRATE = 115200


class LedServer(Board):
    """
    LED control over a socket.

    Used when running in the simulator to control the simulated LEDs.
    """

    @staticmethod
    def get_board_type() -> str:
        """
        Return the type of the board.

        :return: The literal string 'KCHv1B'.
        """
        return 'KCHv1B'

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
        )

        self._identity = self.identify()
        if self._identity.board_type != self.get_board_type():
            raise IncorrectBoardError(self._identity.board_type, self.get_board_type())
        self._serial.set_identity(self._identity)

        # Reset the board to a known state
        self._serial.write('*RESET')

    @classmethod
    def initialise(cls) -> LedServer | None:
        """Initialise the LED server using simulator discovery."""
        # The filter here is the name of the emulated board in the simulator
        boards = get_simulator_boards('LedBoard')

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
                f"Simulator specified LED board at port {board_info.url!r}, "
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

    def set_leds(self, led_num: int, value: tuple[bool, bool, bool]) -> None:
        """Set the colour of the LED."""
        self._serial.write(f'LED:{led_num}:SET:{value[0]:d}:{value[1]:d}:{value[2]:d}')

    def get_leds(self, led_num: int) -> tuple[bool, bool, bool]:
        """Get the colour of the LED."""
        response = self._serial.query(f'LED:{led_num}:GET?')
        red, green, blue = response.split(':')
        return bool(int(red)), bool(int(green)), bool(int(blue))

"""SourceBots Robot Definition."""

import logging

# See https://github.com/j5api/j5/issues/149
import j5.backends.hardware.sr.v4  # noqa: F401
from j5 import BaseRobot, BoardGroup
from j5 import __version__ as j5_version
from j5.backends.hardware import HardwareEnvironment
from j5.boards import Board
from j5.boards.sr.v4 import MotorBoard, PowerBoard, ServoBoard

__version__ = "0.2.0"

LOGGER = logging.getLogger(__name__)


class Robot(BaseRobot):
    """SourceBots robot."""

    def __init__(
            self,
            debug: bool = False,
            wait_start: bool = True,
    ) -> None:
        if debug:
            LOGGER.setLevel(logging.DEBUG)
        LOGGER.info(f"SourceBots API v{__version__}")
        LOGGER.debug("Debug Mode is enabled")
        LOGGER.debug(f"j5 Version: {j5_version}")

        self._power_boards = BoardGroup[PowerBoard](
            HardwareEnvironment.get_backend(PowerBoard),
        )
        self.power_board: PowerBoard = self._power_boards.singular()

        # Power on robot, so that we can find other boards.
        self.power_board.outputs.power_on()

        self._motor_boards = BoardGroup[MotorBoard](
            HardwareEnvironment.get_backend(MotorBoard),
        )
        self.motor_board: MotorBoard = self._motor_boards.singular()

        self._servo_boards = BoardGroup[ServoBoard](
            HardwareEnvironment.get_backend(ServoBoard),
        )
        self.servo_board: ServoBoard = self._servo_boards.singular()

        # Todo: Add Arduino when j5 supports it.
        # Todo: Add game context when j5 supports it.

        for board in Board.BOARDS:
            LOGGER.info(f"Found {board.name}, serial: {board.serial}")
            LOGGER.debug(f"Firmware Version of {board.serial}: {board.firmware_version}")

        if wait_start:
            self.wait_start()

    def wait_start(self) -> None:
        """Wait for the start button to be pressed."""
        LOGGER.info("Waiting for start button.")
        self.power_board.wait_for_start_flash()

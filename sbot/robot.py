"""SourceBots Robot Definition."""

import logging

from j5 import __version__, BaseRobot, BoardGroup
from j5.backends.hardware import HardwareEnvironment
from j5.boards import Board
from j5.boards.sr.v4 import PowerBoard

# See https://github.com/j5api/j5/issues/149
from j5.backends.hardware.sr.v4.power_board import SRV4PowerBoardHardwareBackend # noqa: F401

__version__ = "0.1.0"

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
        LOGGER.debug(f"j5 Version: {__version__}")

        self._power_boards = BoardGroup(PowerBoard, HardwareEnvironment.get_backend(PowerBoard))
        self.power_board: PowerBoard = self._power_boards.singular()

        # Todo: Add Motor Board when j5 supports it.
        # Todo: Add Servo Board when j5 supports it.
        # Todo: Add Arduino when j5 supports it.
        # Todo: Add game context when j5 supports it.

        for board in Board.BOARDS:
            LOGGER.info(f"Found {board.name}, serial: {board.serial}")
            LOGGER.debug(f"Firmware Version of {board.serial}: {board.firmware_version}")

        # Power on robot.
        self.power_board.outputs.power_on()

        if wait_start:
            self.wait_start()

    def wait_start(self) -> None:
        """Wait for the start button to be pressed."""
        LOGGER.info("Waiting for start button.")
        self.power_board.wait_for_start_flash()

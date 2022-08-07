"""SourceBots Robot Definition."""

import logging
from datetime import timedelta
from time import sleep
from typing import Any, Dict, Optional, TypeVar, cast

from j5 import BaseRobot, BoardGroup
from j5 import __version__ as j5_version
from j5.backends import Backend, CommunicationError, Environment
from j5.boards import Board
from j5.boards.sb import SBArduinoBoard
from j5.boards.sr.v4 import MotorBoard, PowerBoard, ServoBoard
from j5.components.piezo import Note
from j5_zoloto import ZolotoCameraBoard

from . import metadata
from .env import HardwareEnvironment
from .timeout import kill_after_delay

__version__ = "0.9.1"

LOGGER = logging.getLogger(__name__)

GAME_LENGTH = 120

BoardT = TypeVar("BoardT", bound=Board)
BackendT = TypeVar("BackendT", bound=Backend)


class Robot(BaseRobot):
    """SourceBots robot."""

    def __init__(
            self,
            *,
            debug: bool = False,
            wait_start: bool = True,
            require_all_boards: bool = True,
            environment: Environment = HardwareEnvironment,
    ) -> None:
        self._require_all_boards = require_all_boards
        self._metadata: Optional[Dict[str, Any]] = None
        self._environment = environment

        if debug:
            LOGGER.setLevel(logging.DEBUG)
        LOGGER.info(f"SourceBots API v{__version__}")
        LOGGER.debug("Debug Mode is enabled")
        LOGGER.debug(f"j5 Version: {j5_version}")

        self._init_power_board()
        self._init_auxilliary_boards()
        self._log_connected_boards()

        if wait_start:
            self.wait_start()

    def _init_power_board(self) -> None:
        self._power_boards = BoardGroup.get_board_group(
            PowerBoard,
            self._environment.get_backend(PowerBoard),
        )
        self.power_board: PowerBoard = self._power_boards.singular()

        # Power on robot, so that we can find other boards.
        self.power_board.outputs.power_on()

    def _init_auxilliary_boards(self) -> None:
        self.motor_boards = self._environment.get_board_group(
            MotorBoard,
        )

        self.servo_boards = self._environment.get_board_group(
            ServoBoard,
        )

        self.arduinos = self._environment.get_board_group(
            SBArduinoBoard,
        )

        self.cameras = self._environment.get_board_group(
            ZolotoCameraBoard,
        )

    def _get_optional_board(
            self,
            board_group: BoardGroup[BoardT, BackendT],
    ) -> Optional[BoardT]:
        try:
            return board_group.singular()
        except CommunicationError:
            if self._require_all_boards:
                raise
            else:
                board_name = board_group.backend_class.board.__name__
                LOGGER.info(f"Did not find a {board_name} (not required)")
                return None

    def _log_connected_boards(self) -> None:
        for board in Board.BOARDS:
            LOGGER.info(f"Found {board.name}, serial: {board.serial_number}")
            LOGGER.debug(
                f"Firmware Version of {board.serial_number}: {board.firmware_version}",
            )

    @property
    def motor_board(self) -> MotorBoard:
        """
        Get the motor board.

        A CommunicationError is raised if there isn't exactly one attached.
        """
        return self.motor_boards.singular()

    @property
    def servo_board(self) -> ServoBoard:
        """
        Get the servo board.

        A CommunicationError is raised if there isn't exactly one attached.
        """
        return self.servo_boards.singular()

    @property
    def arduino(self) -> SBArduinoBoard:
        """
        Get the arduino.

        A CommunicationError is raised if there isn't exactly one attached.
        """
        return self.arduinos.singular()

    @property
    def camera(self) -> ZolotoCameraBoard:
        """
        Get the robot's camera interface.

        :returns: a :class:`j5_zoloto.board.ZolotoCameraBoard`.
        """
        return self.cameras.singular()

    # Metadata

    @property
    def metadata(self) -> Dict[str, Any]:
        """The game metadata."""
        if self._metadata is None:
            raise metadata.MetadataNotReadyError()
        else:
            return self._metadata

    @property
    def zone(self) -> int:
        """The robot's starting zone in the arena (0, 1, 2 or 3)."""
        try:
            return cast(int, self.metadata["zone"])
        except KeyError:
            raise metadata.MetadataKeyError("zone") from None

    @property
    def is_competition(self) -> bool:
        """Whether the robot is in a competition or development environment."""
        try:
            return cast(bool, self.metadata["is_competition"])
        except KeyError:
            raise metadata.MetadataKeyError("is_competition") from None

    def sleep(self, secs: float) -> None:
        """Pause the program for secs seconds."""
        sleep(secs)

    # Custom functionality

    def wait_start(self) -> None:
        """Wait for the start button to be pressed."""
        LOGGER.info("Waiting for start button.")
        self.power_board.piezo.buzz(timedelta(seconds=0.1), Note.A6)
        self.power_board.wait_for_start_flash()
        LOGGER.info("Start button pressed.")

        default_metadata: Dict[str, Any] = {
            "is_competition": False,
            "zone": 0,
        }
        self._metadata = metadata.load(fallback=default_metadata)

        if self.is_competition:
            kill_after_delay(GAME_LENGTH)

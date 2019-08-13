"""SourceBots Robot Definition."""

import logging
import warnings
from datetime import timedelta
from typing import Any, Dict, Optional, TypeVar, cast

# See https://github.com/j5api/j5/issues/149
import j5.backends.hardware.sb.arduino  # noqa: F401
import j5.backends.hardware.sr.v4  # noqa: F401
from j5 import BaseRobot, BoardGroup
from j5 import __version__ as j5_version
from j5.backends import CommunicationError
from j5.backends.hardware import HardwareEnvironment
from j5.boards import Board
from j5.boards.sb import SBArduinoBoard
from j5.boards.sr.v4 import MotorBoard, PowerBoard, ServoBoard
from j5.components import MarkerCamera
from j5.components.piezo import Note

from . import metadata
from .timeout import kill_after_delay

try:
    import j5.backends.hardware.zoloto  # noqa: F401
    from j5.boards.zoloto import ZolotoCameraBoard
    from .vision import SbotCameraBackend
    ENABLE_VISION = True
except ImportError:
    warnings.warn(
        "Zoloto not installed, disabling vision support",
        category=ImportWarning,
    )
    ENABLE_VISION = False

__version__ = "0.6.0"

LOGGER = logging.getLogger(__name__)

GAME_LENGTH = 120

T = TypeVar("T", bound=Board)


class Robot(BaseRobot):
    """SourceBots robot."""

    def __init__(
            self,
            debug: bool = False,
            wait_start: bool = True,
            require_all_boards: bool = True,
    ) -> None:
        self._require_all_boards = require_all_boards

        if debug:
            LOGGER.setLevel(logging.DEBUG)
        LOGGER.info(f"SourceBots API v{__version__}")
        LOGGER.debug("Debug Mode is enabled")
        LOGGER.debug(f"j5 Version: {j5_version}")

        self._init_power_board()
        self._init_auxilliary_boards()
        self._log_connected_boards()

        default_metadata: Dict[str, Any] = {
            "is_competition": False,
            "zone": 0,
        }

        self.metadata = metadata.load(fallback=default_metadata)

        if wait_start:
            self.wait_start()

    def _init_power_board(self) -> None:
        self._power_boards = BoardGroup[PowerBoard](
            HardwareEnvironment.get_backend(PowerBoard),
        )
        self.power_board: PowerBoard = self._power_boards.singular()

        # Power on robot, so that we can find other boards.
        self.power_board.outputs.power_on()

    def _init_auxilliary_boards(self) -> None:
        self.motor_boards = BoardGroup[MotorBoard](
            HardwareEnvironment.get_backend(MotorBoard),
        )

        self.servo_boards = BoardGroup[ServoBoard](
            HardwareEnvironment.get_backend(ServoBoard),
        )

        self.arduinos = BoardGroup[SBArduinoBoard](
            HardwareEnvironment.get_backend(SBArduinoBoard),
        )

        if ENABLE_VISION:

            self._cameras = BoardGroup[ZolotoCameraBoard](
                SbotCameraBackend,
            )

            self._camera: Optional[ZolotoCameraBoard] = (
                self._get_optional_board(self._cameras)
            )

    def _get_optional_board(self, board_group: BoardGroup[T]) -> Optional[T]:
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
            LOGGER.info(f"Found {board.name}, serial: {board.serial}")
            LOGGER.debug(f"Firmware Version of {board.serial}: {board.firmware_version}")

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
    def camera(self) -> Optional[MarkerCamera]:
        """Alias to the camera."""
        if self._camera is None:
            return None
        else:
            return self._camera.camera

    # Metadata

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

    # Custom functionality

    def wait_start(self) -> None:
        """Wait for the start button to be pressed."""
        LOGGER.info("Waiting for start button.")
        self.power_board.piezo.buzz(timedelta(seconds=0.1), Note.A6)
        self.power_board.wait_for_start_flash()
        LOGGER.info("Start button pressed.")

        if self.is_competition:
            kill_after_delay(GAME_LENGTH)

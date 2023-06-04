from __future__ import annotations

import logging
from time import sleep

from april_vision.examples.camera import AprilCamera, setup_cameras

from . import game_specific, metadata, timeout
from ._version import __version__
from .exceptions import MetadataNotReadyError
from .logging import TRACE
from .metadata import Metadata
from .motor_board import MotorBoard
from .power_board import Note, PowerBoard
from .servo_board import ServoBoard
from .utils import obtain_lock, singular

logger = logging.getLogger(__name__)


def setup_logging(debug_logging: bool, trace_logging: bool) -> None:
    logformat = '%(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(fmt=logformat)
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    if trace_logging:
        root_logger.setLevel(TRACE)
        logger.log(TRACE, "Trace Mode is enabled")
    elif debug_logging:
        root_logger.setLevel(logging.DEBUG)
        logger.debug("Debug Mode is enabled")
    else:
        root_logger.setLevel(logging.INFO)


class Robot:
    def __init__(
        self,
        *,
        debug: bool = False,
        wait_start: bool = True,
        trace_logging: bool = False,
    ) -> None:
        self._lock = obtain_lock()
        self._metadata: Metadata | None = None

        setup_logging(debug, trace_logging)

        logger.info(f"SourceBots API v{__version__}")

        self._init_power_board()
        self._init_aux_boards()
        self._init_camera()
        # TODO log connected boards

        if wait_start:
            self.wait_start()

    def _init_power_board(self) -> None:
        power_boards = PowerBoard._get_supported_boards()
        self._power_board = singular(power_boards)
        self._power_board.outputs.power_on()
        # TODO delay for boards to power up ???

    def _init_aux_boards(self) -> None:
        self._motor_boards = MotorBoard._get_supported_boards()
        self._servo_boards = ServoBoard._get_supported_boards()

    def _init_camera(self) -> None:
        self._cameras = setup_cameras(game_specific.MARKER_SIZES)

    @property
    def power_board(self) -> PowerBoard:
        return self._power_board

    @property
    def motor_boards(self) -> dict[str, MotorBoard]:
        return self._motor_boards

    @property
    def motor_board(self) -> MotorBoard:
        return singular(self._motor_boards)

    @property
    def servo_boards(self) -> dict[str, ServoBoard]:
        return self._servo_boards

    @property
    def servo_board(self) -> ServoBoard:
        return singular(self._servo_boards)

    @property
    def camera(self) -> AprilCamera:
        return singular(self._cameras)

    def sleep(self, secs: float) -> None:
        sleep(secs)

    @property
    def metadata(self) -> Metadata:
        if self._metadata is None:
            raise MetadataNotReadyError()
        else:
            return self._metadata

    @property
    def zone(self) -> int:
        return self.metadata['zone']

    @property
    def is_competition(self) -> bool:
        return self.metadata['is_competition']

    def wait_start(self) -> None:
        # ignore previous button presses
        _ = self.power_board._start_button()
        logger.info('Waiting for start button.')

        self.power_board.piezo.buzz(0.1, Note.A6)
        self.power_board._run_led.flash()

        while not self.power_board._start_button():
            sleep(0.1)
        logger.info("Start button pressed.")
        self.power_board._run_led.on()

        self._metadata = metadata.load()

        if self.is_competition:
            timeout.kill_after_delay(game_specific.GAME_LENGTH)


# TODO double check logging handlers
# TODO error handling
# TODO add all the logging
# TODO repr/str on all the things

# TODO immutable dict

# TODO add atexits for boards
# TODO game timeout
# TODO arduino support

from __future__ import annotations

import itertools
import logging
from time import sleep
from types import MappingProxyType
from typing import Mapping

from . import game_specific, metadata, timeout
from ._version import __version__
from .arduino import Arduino
from .camera import AprilCamera, setup_cameras
from .exceptions import MetadataNotReadyError
from .logging import log_to_debug, setup_logging
from .metadata import Metadata
from .motor_board import MotorBoard
from .power_board import Note, PowerBoard
from .servo_board import ServoBoard
from .utils import obtain_lock, singular

logger = logging.getLogger(__name__)


class Robot:
    __slots__ = (
        '_lock', '_metadata', '_power_board', '_motor_boards', '_servo_boards',
        '_arduinos', '_cameras',
    )

    def __init__(
        self,
        *,
        debug: bool = False,
        wait_start: bool = True,
        trace_logging: bool = False,
        manual_boards: dict[str, list[str]] | None = None,
    ) -> None:
        self._lock = obtain_lock()
        self._metadata: Metadata | None = None

        setup_logging(debug, trace_logging)

        logger.info(f"SourceBots API v{__version__}")

        if manual_boards:
            self._init_power_board(manual_boards.get(PowerBoard.get_board_type(), []))
            self._init_aux_boards(manual_boards)
        else:
            self._init_power_board()
            self._init_aux_boards()
        self._init_camera()
        self._log_connected_boards()

        if wait_start:
            self.wait_start()

    def _init_power_board(self, manual_boards: list[str] | None = None) -> None:
        power_boards = PowerBoard._get_supported_boards(manual_boards)
        self._power_board = singular(power_boards)
        self._power_board.outputs.power_on()
        # TODO delay for boards to power up ???

    def _init_aux_boards(self, manual_boards: dict[str, list[str]] | None = None) -> None:
        if manual_boards is None:
            manual_boards = {}

        manual_motorboards = manual_boards.get(MotorBoard.get_board_type(), [])
        manual_servoboards = manual_boards.get(ServoBoard.get_board_type(), [])
        manual_arduinos = manual_boards.get(Arduino.get_board_type(), [])

        self._motor_boards = MotorBoard._get_supported_boards(manual_motorboards)
        self._servo_boards = ServoBoard._get_supported_boards(manual_servoboards)
        self._arduinos = Arduino._get_supported_boards(manual_arduinos)

    def _init_camera(self) -> None:
        self._cameras = MappingProxyType(setup_cameras(game_specific.MARKER_SIZES))

    def _log_connected_boards(self) -> None:
        boards = itertools.chain(
            [self.power_board],
            self.motor_boards.values(),
            self.servo_boards.values(),
            self.arduinos.values(),
            self._cameras.values(),
        )
        for board in boards:
            identity = board.identify()
            board_type = board.__class__.__name__
            logger.info(f"Found {board_type}, serial: {identity.asset_tag}")
            logger.debug(
                f"Firmware Version of {identity.asset_tag}: {identity.sw_version}, "
                f"reported type: {identity.board_type}",
            )

    @property
    def power_board(self) -> PowerBoard:
        return self._power_board

    @property
    def motor_boards(self) -> Mapping[str, MotorBoard]:
        return self._motor_boards

    @property
    def motor_board(self) -> MotorBoard:
        return singular(self._motor_boards)

    @property
    def servo_boards(self) -> Mapping[str, ServoBoard]:
        return self._servo_boards

    @property
    def servo_board(self) -> ServoBoard:
        return singular(self._servo_boards)

    @property
    def arduinos(self) -> Mapping[str, Arduino]:
        return self._arduinos

    @property
    def arduino(self) -> Arduino:
        return singular(self._arduinos)

    @property
    def camera(self) -> AprilCamera:
        return singular(self._cameras)

    @log_to_debug
    def sleep(self, secs: float) -> None:
        sleep(secs)

    @property
    @log_to_debug
    def metadata(self) -> Metadata:
        if self._metadata is None:
            raise MetadataNotReadyError()
        else:
            return self._metadata

    @property
    @log_to_debug
    def zone(self) -> int:
        return self.metadata['zone']

    @property
    @log_to_debug
    def is_competition(self) -> bool:
        return self.metadata['is_competition']

    @log_to_debug
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

# TODO docstrings

"""The main entry point for the sbot package."""
from __future__ import annotations

import itertools
import logging
from time import sleep
from types import MappingProxyType
from typing import Mapping

from . import game_specific, metadata, timeout
from ._version import __version__
from .arduino import Arduino
from .camera import AprilCamera, _setup_cameras
from .exceptions import MetadataNotReadyError
from .logging import log_to_debug, setup_logging
from .metadata import Metadata
from .motor_board import MotorBoard
from .power_board import Note, PowerBoard
from .servo_board import ServoBoard
from .utils import obtain_lock, singular

logger = logging.getLogger(__name__)


class Robot:
    """
    The main robot class that provides access to all the boards.

    There can be only one instance of this class active in your operating
    system at a time, creating a second instance will raise an OSError.

    :param debug: Enable debug logging to the console, defaults to False
    :param wait_for_start: Wait in the constructor until the start button is pressed,
        defaults to True
    :param trace_logging: Enable trace level logging to the console, defaults to False
    :param manual_boards: A dictionary of board types to a list of serial port paths
        to allow for connecting to boards that are not automatically detected, defaults to None
    """
    __slots__ = (
        '_lock', '_metadata', '_power_board', '_motor_boards', '_servo_boards',
        '_arduinos', '_cameras',
    )

    def __init__(
        self,
        *,
        debug: bool = False,
        wait_for_start: bool = True,
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

        if wait_for_start:
            self.wait_start()

    def _init_power_board(self, manual_boards: list[str] | None = None) -> None:
        """
        Locate the PowerBoard and enable all the outputs to power the other boards.

        :param manual_boards: Serial port paths to also check for power boards,
            defaults to None
        :raises RuntimeError: If exactly one PowerBoard is not found
        """
        power_boards = PowerBoard._get_supported_boards(manual_boards)
        self._power_board = singular(power_boards)
        self._power_board.outputs.power_on()
        # TODO delay for boards to power up ???

    def _init_aux_boards(self, manual_boards: dict[str, list[str]] | None = None) -> None:
        """
        Locate the motor boards, servo boards, and Arduinos.

        All boards are located automatically, but additional serial ports can be
        provided using the manual_boards parameter. Located boards are queried for
        their identity and firmware version.

        :param manual_boards:  A dictionary of board types to a list of additional
            serial port paths that should be checked for boards of that type, defaults to None
        """
        if manual_boards is None:
            manual_boards = {}

        manual_motorboards = manual_boards.get(MotorBoard.get_board_type(), [])
        manual_servoboards = manual_boards.get(ServoBoard.get_board_type(), [])
        manual_arduinos = manual_boards.get(Arduino.get_board_type(), [])

        self._motor_boards = MotorBoard._get_supported_boards(manual_motorboards)
        self._servo_boards = ServoBoard._get_supported_boards(manual_servoboards)
        self._arduinos = Arduino._get_supported_boards(manual_arduinos)

    def _init_camera(self) -> None:
        """
        Locate cameras that we have calibration data for.

        These cameras are used for AprilTag detection and provide location data of
        markers in its field of view.
        """
        self._cameras = MappingProxyType(_setup_cameras(game_specific.MARKER_SIZES))

    def _log_connected_boards(self) -> None:
        """
        Log the board types and serial numbers of all the boards connected to the robot.

        Firmware versions are also logged at debug level.
        """
        boards = itertools.chain(
            [self.power_board],  # we only have one power board so make it iterable
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
        """
        Access the power board connected to the robot.

        :return: The power board object
        """
        return self._power_board

    @property
    def motor_boards(self) -> Mapping[str, MotorBoard]:
        """
        Access the motor boards connected to the robot.

        These are indexed by their serial number.

        :return: A mapping of serial numbers to motor boards
        """
        return self._motor_boards

    @property
    def motor_board(self) -> MotorBoard:
        """
        Access the motor board connected to the robot.

        This can only be used if there is exactly one motor board connected.

        :return: The motor board object
        :raises RuntimeError: If there is not exactly one motor board connected
        """
        return singular(self._motor_boards)

    @property
    def servo_boards(self) -> Mapping[str, ServoBoard]:
        """
        Access the servo boards connected to the robot.

        These are indexed by their serial number.

        :return: A mapping of serial numbers to servo boards
        """
        return self._servo_boards

    @property
    def servo_board(self) -> ServoBoard:
        """
        Access the servo board connected to the robot.

        This can only be used if there is exactly one servo board connected.

        :return: The servo board object
        :raises RuntimeError: If there is not exactly one servo board connected
        """
        return singular(self._servo_boards)

    @property
    def arduinos(self) -> Mapping[str, Arduino]:
        """
        Access the Arduinos connected to the robot.

        These are indexed by their serial number.

        :return: A mapping of serial numbers to Arduinos
        """
        return self._arduinos

    @property
    def arduino(self) -> Arduino:
        """
        Access the Arduino connected to the robot.

        This can only be used if there is exactly one Arduino connected.

        :return: The Arduino object
        :raises RuntimeError: If there is not exactly one Arduino connected
        """
        return singular(self._arduinos)

    @property
    def camera(self) -> AprilCamera:
        """
        Access the camera connected to the robot.

        This can only be used if there is exactly one camera connected.
        The robot class currently only supports one camera.

        :return: The camera object
        :raises RuntimeError: If there is not exactly one camera connected
        """
        return singular(self._cameras)

    @log_to_debug
    def sleep(self, secs: float) -> None:
        """
        Sleep for a number of seconds.

        This is a convenience method that can be used instead of time.sleep().

        :param secs: The number of seconds to sleep for
        """
        sleep(secs)

    @property
    @log_to_debug
    def metadata(self) -> Metadata:
        """
        Fetch the robot's current metadata.

        See the metadata module for more information.

        :raises MetadataNotReadyError: If the start button has not been pressed yet
        :return: The metadata dictionary
        """
        if self._metadata is None:
            raise MetadataNotReadyError()
        else:
            return self._metadata

    @property
    @log_to_debug
    def zone(self) -> int:
        """
        Get the zone that the robot is in.

        :return: The robot's zone number
        :raises MetadataNotReadyError: If the start button has not been pressed yet
        """
        return self.metadata['zone']

    @property
    @log_to_debug
    def is_competition(self) -> bool:
        """
        Find out if the robot is in competition mode.

        :return: Whether the robot is in competition mode
        :raises MetadataNotReadyError: If the start button has not been pressed yet
        """
        return self.metadata['is_competition']

    @log_to_debug
    def wait_start(self) -> None:
        """
        Wait for the start button to be pressed.

        The power board will beep once when waiting for the start button.
        The power board's run LED will flash while waiting for the start button.
        Once the start button is pressed, the metadata will be loaded and the timeout
        will start if in competition mode.
        """
        # ignore previous button presses
        _ = self.power_board._start_button()
        logger.info('Waiting for start button.')

        self.power_board.piezo.buzz(0.1, Note.A6)
        self.power_board._run_led.flash()

        while not self.power_board._start_button():
            sleep(0.1)
        logger.info("Start button pressed.")
        self.power_board._run_led.on()

        if self._metadata is None:
            self._metadata = metadata.load()

        if self.is_competition:
            timeout.kill_after_delay(game_specific.GAME_LENGTH)

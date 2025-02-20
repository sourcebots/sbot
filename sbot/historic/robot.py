"""The main entry point for the sbot package."""
from __future__ import annotations

import itertools
import logging
from socket import socket
from time import sleep
from types import MappingProxyType
from typing import Literal, Mapping

from sbot._version import __version__
from sbot.simulator.time_server import TimeServer

from .. import game_specific
from ..internal import timeout
from ..internal.exceptions import MetadataNotReadyError
from ..internal.logging import log_to_debug, setup_logging
from . import metadata
from .arduino import Arduino
from .camera import AprilCamera, _setup_cameras
from .leds import LED, StartLed, get_user_leds
from .metadata import Metadata
from .motor_board import MotorBoard
from .power_board import Note, PowerBoard
from .servo_board import ServoBoard
from .utils import IN_SIMULATOR, ensure_atexit_on_term, obtain_lock, singular

try:
    from ..internal.mqtt import (
        MQTT_VALID,
        MQTTClient,
        RemoteStartButton,
        get_mqtt_variables,
    )
except ImportError:
    MQTT_VALID = False

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
    :param no_powerboard: If True, initialize the robot without a powerboard, defaults to False
    """

    __slots__ = (
        '_arduinos', '_cameras', '_lock', '_metadata', '_motor_boards', '_mqttc', '_no_pb',
        '_power_board', '_servo_boards', '_start_button', '_start_led', '_time_server',
        '_user_leds')

    def __init__(
        self,
        *,
        debug: bool = False,
        wait_for_start: bool = True,
        trace_logging: bool = False,
        manual_boards: dict[str, list[str]] | None = None,
        no_powerboard: bool = False,
    ) -> None:
        self._lock: TimeServer | socket | None
        if IN_SIMULATOR:
            self._lock = TimeServer.initialise()
            if self._lock is None:
                raise OSError(
                    'Unable to obtain lock, Is another robot instance already running?'
                )
        else:
            self._lock = obtain_lock()
        self._metadata: Metadata | None = None
        self._no_pb = no_powerboard

        setup_logging(debug, trace_logging)
        ensure_atexit_on_term()

        logger.info(f"SourceBots API v{__version__}")

        if MQTT_VALID:
            # get the config from env vars
            mqtt_config = get_mqtt_variables()
            self._mqttc = MQTTClient.establish(**mqtt_config)
            self._start_button = RemoteStartButton(self._mqttc)

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
        if not self._no_pb:
            power_boards = PowerBoard._get_supported_boards(manual_boards)  # noqa: SLF001
            self._power_board = singular(power_boards)
            self._power_board.outputs.power_on()

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

        self._motor_boards = MotorBoard._get_supported_boards(manual_motorboards)  # noqa: SLF001
        self._servo_boards = ServoBoard._get_supported_boards(manual_servoboards)  # noqa: SLF001
        self._arduinos = Arduino._get_supported_boards(manual_arduinos)  # noqa: SLF001

        self._user_leds = get_user_leds()
        self._start_led = StartLed()

    def _init_camera(self) -> None:
        """
        Locate cameras that we have calibration data for.

        These cameras are used for AprilTag detection and provide location data of
        markers in its field of view.
        """
        if MQTT_VALID:
            self._cameras = MappingProxyType(_setup_cameras(
                game_specific.MARKER_SIZES,
                self._mqttc.wrapped_publish,
            ))
        else:
            self._cameras = MappingProxyType(_setup_cameras(game_specific.MARKER_SIZES))

    def _log_connected_boards(self) -> None:
        """
        Log the board types and serial numbers of all the boards connected to the robot.

        Firmware versions are also logged at debug level.
        """
        # we only have one power board so make it iterable
        power_board = [] if self._no_pb else [self.power_board]
        boards = itertools.chain(
            power_board,
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
        if not self._no_pb:
            return self._power_board
        else:
            raise RuntimeError("No power board was initialized")

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

    @property
    def leds(self) -> Mapping[Literal['A', 'B', 'C'], LED]:
        """
        Access the user LEDs connected to the robot.

        :return: A mapping of colours to user LEDs
        """
        return self._user_leds

    @log_to_debug
    def sleep(self, secs: float) -> None:
        """
        Sleep for a number of seconds.

        This is a convenience method that can be used instead of time.sleep().

        :param secs: The number of seconds to sleep for
        """
        if IN_SIMULATOR:
            assert isinstance(self._lock, TimeServer)
            self._lock.sleep(secs)
        else:
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
        def null_button_pressed() -> bool:
            return False

        if MQTT_VALID:
            remote_start_pressed = self._start_button.get_start_button_pressed
        else:
            remote_start_pressed = null_button_pressed

        if not self._no_pb:
            start_button_pressed = self.power_board._start_button  # noqa: SLF001
        else:
            # null out the start button function
            start_button_pressed = null_button_pressed

        # ignore previous button presses
        _ = start_button_pressed()
        _ = remote_start_pressed()
        logger.info('Waiting for start button.')

        if not self._no_pb:
            self.power_board.piezo.buzz(Note.A6, 0.1)
            self.power_board._run_led.flash()  # noqa: SLF001
        self._start_led.flash_start()

        while not start_button_pressed() and not remote_start_pressed():
            self.sleep(0.1)
        logger.info("Start button pressed.")

        if not self._no_pb:
            self.power_board._run_led.on()  # noqa: SLF001
        self._start_led.set_state(False)

        if self._metadata is None:
            self._metadata = metadata.load()

        # Simulator timeout is handled by the simulator supervisor
        if self.is_competition and not IN_SIMULATOR:
            timeout.kill_after_delay(game_specific.GAME_LENGTH)

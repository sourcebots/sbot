"""A collection of utility methods for general robot functions."""
from __future__ import annotations

import logging
import time
from enum import IntEnum

from ._comp import Comp
from .game_specific import GAME_LENGTH
from .internal.board_manager import IN_SIMULATOR, BoardManager, DiscoveryTemplate
from .internal.overrides import get_overrides
from .internal.start_led import flash_start_led, set_start_led
from .internal.timeout import kill_after_delay
from .internal.utils import float_bounds_check

try:
    from .internal.mqtt import MQTT_VALID, RemoteStartButton
except ImportError:
    MQTT_VALID = False

logger = logging.getLogger(__name__)


class Utils:
    """A collection of utility methods for general robot functions."""

    __slots__ = ('_boards', '_comp', '_remote_start')

    def __init__(self, boards: BoardManager, comp: Comp):
        self._boards = boards
        template = DiscoveryTemplate(
            identifier='time',
            name='time server',
            vid=0,  # Unused
            pid=0,  # Unused
            board_type='TimeServer',
            sim_only=True,
            sim_board_type='TimeServer',
            max_boards=1,
            timeout=None,  # Disable timeout
        )
        BoardManager.register_board(template)
        # We need to trigger loading the metadata when wait_start is called
        self._comp = comp

        if MQTT_VALID:
            self._remote_start: RemoteStartButton | None = None
            if boards.mqtt:
                self._remote_start = RemoteStartButton(boards.mqtt)
        else:
            self._remote_start = None

    def sleep(self, duration: float) -> None:
        """
        Sleep for a number of seconds.

        This is a convenience method that can be used instead of time.sleep().

        :param secs: The number of seconds to sleep for
        """
        if IN_SIMULATOR:
            if duration < 0:
                raise ValueError("sleep length must be non-negative")
            time_server = self._boards.get_first_board('time')
            # This command will block until the sleep is complete
            time_server.write(f'SLEEP:{duration * 1000:.0f}')
        else:
            time.sleep(duration)

    def wait_start(self) -> None:
        """
        Wait for the start button to be pressed.

        The power board will beep once when waiting for the start button.
        The power board's run LED will flash while waiting for the start button.
        Once the start button is pressed, the metadata will be loaded and the timeout
        will start if in competition mode.

        Boards will be loaded if they have not already been loaded.
        """
        if not self._boards.loaded:
            self.load_boards()

        def null_button_pressed() -> bool:
            return False

        def check_physical_start_button() -> bool:
            power_board = self._boards.get_first_board('power')
            response: str = power_board.query('BTN:START:GET?')
            internal, external = response.split(':')
            return (internal == '1') or (external == '1')

        overrides = get_overrides()
        no_powerboard = overrides.get('NO_POWERBOARD', "0") == "1"

        if self._remote_start is not None:
            remote_start_pressed = self._remote_start.get_start_button_pressed
        else:
            remote_start_pressed = null_button_pressed

        if not no_powerboard:
            power_board = self._boards.get_first_board('power')
            start_button_pressed = check_physical_start_button
        else:
            # null out the start button function
            start_button_pressed = null_button_pressed

        # Clear the physical and remote start button state
        start_button_pressed()
        remote_start_pressed()

        logger.info('Waiting for start button.')
        flash_start_led()
        if not no_powerboard:
            self.sound_buzzer(Note.C6, 0.1)
            # enable flashing the run LED
            power_board.write('LED:RUN:SET:F')

        # wait for the start button to be pressed
        while not start_button_pressed() and not remote_start_pressed():
            self.sleep(0.1)
        logger.info("Start button pressed.")

        if not no_powerboard:
            # disable flashing the run LED
            power_board.write('LED:RUN:SET:0')

        set_start_led(False)  # disable flashing the KCH start LED
        self._comp._load()  # noqa: SLF001, load the metadata

        # Simulator timeout is handled by the simulator supervisor
        if self._comp.is_competition and not IN_SIMULATOR:
            kill_after_delay(GAME_LENGTH)

    def sound_buzzer(self, frequency: int, duration: float) -> None:
        """
        Produce a tone on the piezo buzzer.

        This method is non-blocking, and sending another tone while one is
        playing will cancel the first.

        :param frequency: The frequency of the tone, in Hz.
        :param duration: The duration of the tone, in seconds.
        :raise RuntimeError: If no power boards are connected.
        """
        # Previously power_board.piezo.buzz
        power_boards = self._boards.get_boards('power')
        if len(power_boards) == 0:
            raise RuntimeError("No power boards connected")
        board = list(power_boards.values())[0]

        frequency_int = int(float_bounds_check(
            frequency, 8, 10_000, "Frequency is a float in Hz between 0 and 10000"))
        duration_ms = int(float_bounds_check(
            duration * 1000, 0, 2**31 - 1,
            f"Duration is a float in seconds between 0 and {(2**31 - 1) / 1000:,.0f}"))

        cmd = f'NOTE:{frequency_int}:{duration_ms}'
        board.write(cmd)

    def load_boards(self) -> None:
        """
        Trigger board discovery to run.

        This is automatically called by wait_start, but can be called manually.

        :raise RuntimeError: If boards have already been loaded.
        """
        if not self._boards.loaded:
            self._boards.load_boards()
            self._boards.populate_outputs()
            self._boards.load_cameras()
        else:
            raise RuntimeError("Boards have already been loaded")

        self._boards.log_connected_boards(True)


class Note(IntEnum):
    """
    An enumeration of notes.

    An enumeration of notes from scientific pitch
    notation and their related frequencies in Hz.
    """

    C6 = 1047
    D6 = 1175
    E6 = 1319
    F6 = 1397
    G6 = 1568
    A6 = 1760
    B6 = 1976
    C7 = 2093
    D7 = 2349
    E7 = 2637
    F7 = 2794
    G7 = 3136
    A7 = 3520
    B7 = 3951
    C8 = 4186

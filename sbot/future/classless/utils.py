from __future__ import annotations

from typing import NamedTuple

from sbot.serial_wrapper import SerialWrapper

from .comp import Comp


class Utils:
    def __init__(self, boards: BoardManager, comp: Comp):
        self._boards = boards
        # We need to trigger loading the metadata when wait_start is called
        self._comp = comp

    def sleep(self, duration: float) -> None:
        pass

    def wait_start(self) -> None:
        pass

    def sound_buzzer(self, frequency: int, duration: int) -> None:
        # Previously power_board.piezo.buzz
        pass

    def load_boards(self) -> None:
        self._boards.load_boards()


class BoardIdentifier(NamedTuple):
    """An identifier for a single output on a board."""

    port: SerialWrapper
    idx: int


class BoardManager:
    power: list[BoardIdentifier]
    motors: list[BoardIdentifier]
    servos: list[BoardIdentifier]
    # Contains at most one arduino board
    arduino: SerialWrapper | None = None
    # vision
    leds: list[BoardIdentifier]

    # TODO all discovery and cleanup functions

    def load_boards(self) -> None:
        pass

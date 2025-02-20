"""General utility functions and classes for the sbot package."""
from __future__ import annotations

import logging
import os
import signal
from abc import ABC, abstractmethod
from types import FrameType
from typing import Any, NamedTuple

from serial.tools.list_ports_common import ListPortInfo

logger = logging.getLogger(__name__)

IN_SIMULATOR = os.environ.get('WEBOTS_SIMULATOR', '') == '1'


class BoardIdentity(NamedTuple):
    """
    A container for the identity of a board.

    All the board firmwares should return this information in response to
    the *IDN? query.

    :param manufacturer: The manufacturer of the board
    :param board_type: The short name of the board, i.e. PBv4B
    :param asset_tag: The asset tag of the board,
        this should match what is printed on the board
    :param sw_version: The firmware version of the board
    """

    manufacturer: str = ""
    board_type: str = ""
    asset_tag: str = ""
    sw_version: str = ""


class BoardInfo(NamedTuple):
    """A container for the information about a board connection."""

    url: str
    serial_number: str
    type_str: str


class Board(ABC):
    """
    The base class for all boards.

    Slots are used to prevent adding attributes to the class at runtime.
    They must also be defined in subclasses.
    """

    __slots__ = ('_identity',)

    @staticmethod
    @abstractmethod
    def get_board_type() -> str:
        """
        The string that is expected to be returned by the board's firmware.

        This should match the value in the board_type field of the response to
        the *IDN? query. This is implemented as a static method because class-level
        attributes are not compatible with slots.

        :return: The board type name
        """
        pass  # pragma: no cover

    @abstractmethod
    def identify(self) -> BoardIdentity:
        """
        Return the board's identity as reported by the firmware.

        :return: The board's identity
        """
        pass  # pragma: no cover


def map_to_int(
        x: float,
        in_min: float,
        in_max: float,
        out_min: int,
        out_max: int,
) -> int:
    """
    Map a value from the input range to the output range, returning the value as an int.

    This is used to convert a float value to an integer value for sending to the board.

    :param x: The value to map
    :param in_min: The lower bound of the input range
    :param in_max: The upper bound of the input range
    :param out_min: The lower bound of the output range
    :param out_max: The upper bound of the output range
    :return: The mapped value
    """
    value = (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
    return int(value)


def map_to_float(
        x: int,
        in_min: int,
        in_max: int,
        out_min: float,
        out_max: float,
        precision: int = 3,
) -> float:
    """
    Map a value from the input range to the output range, returning the value as a float.

    This is used to convert an integer value from the board to a float value.

    :param x: The value to map
    :param in_min: The lower bound of the input range
    :param in_max: The upper bound of the input range
    :param out_min: The lower bound of the output range
    :param out_max: The upper bound of the output range
    :param precision: The number of decimal places to round the output to, defaults to 3
    :return: The mapped value
    """
    value = (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
    return round(value, precision)


def float_bounds_check(value: Any, min_val: float, max_val: float, err_msg: str) -> float:
    """
    Test that a value can be converted to a float and is within the given bounds.

    Errors are caught and re-raised with a more descriptive message.

    :param value: The value to test
    :param min_val: The minimum allowed value
    :param max_val: The maximum allowed value
    :param err_msg: The error message to raise if the value is invalid or out of bounds
    :raises TypeError: If the value cannot be converted to a float
    :raises ValueError: If the value is out of bounds
    :return: The input value converted to a float
    """
    try:
        new_val = float(value)
    except ValueError as e:
        raise TypeError(err_msg) from e

    if (new_val < min_val) or (new_val > max_val):
        raise ValueError(err_msg)

    return new_val


def get_USB_identity(port: ListPortInfo) -> BoardIdentity:
    """
    Generate an approximate identity for a board using the USB descriptor.

    This data will be overridden by the firmware once communication is established,
    but is used for early logging messages and error handling.

    :param port: The USB port information from pyserial
    :return: An initial identity for the board
    """
    try:
        return BoardIdentity(
            manufacturer=port.manufacturer or "",
            board_type=port.product or "",
            asset_tag=port.serial_number or "",
        )
    except Exception:
        logger.warning(
            f"Failed to pull identifying information from serial device {port.device}")
        return BoardIdentity()


def ensure_atexit_on_term() -> None:
    """
    Ensure `atexit` triggers on `SIGTERM`.

    > The functions registered via [`atexit`] are not called when the program is
      killed by a signal not handled by Python
    """
    if signal.getsignal(signal.SIGTERM) != signal.SIG_DFL:
        # If a signal handler is already present for SIGTERM,
        # this is sufficient for `atexit` to trigger, so do nothing.
        return

    def handle_signal(handled_signum: int, frame: FrameType | None) -> None:
        """
        Handle the given signal by outputting some text and terminating the process.

        This will trigger `atexit`.
        """
        logger.info(signal.strsignal(handled_signum))
        exit(1)

    # Add the null-ish signal handler
    signal.signal(signal.SIGTERM, handle_signal)


def get_simulator_boards(board_filter: str = '') -> list[BoardInfo]:
    """
    Get a list of all boards configured in the simulator.

    This is used to support discovery of boards in the simulator environment.

    :param board_filter: A filter to only return boards of a certain type
    :return: A list of board connection information
    """
    if 'WEBOTS_ROBOT' not in os.environ:
        return []

    simulator_data = os.environ['WEBOTS_ROBOT'].splitlines()
    simulator_boards = []

    for board_data in simulator_data:
        board_data = board_data.rstrip('/')
        board_fragment, serial_number = board_data.rsplit('/', 1)
        board_url, board_type = board_fragment.rsplit('/', 1)

        board_info = BoardInfo(url=board_url, serial_number=serial_number, type_str=board_type)

        if board_filter and board_info.type_str != board_filter:
            continue

        simulator_boards.append(board_info)

    return simulator_boards

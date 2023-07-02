"""General utility functions and classes for the sbot package."""
from __future__ import annotations

import logging
import socket
from abc import ABC, abstractmethod
from typing import Any, Mapping, NamedTuple, TypeVar

from serial.tools.list_ports_common import ListPortInfo

T = TypeVar('T')
logger = logging.getLogger(__name__)


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


class Board(ABC):
    """
    This is the base class for all boards.

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


def singular(container: Mapping[str, T]) -> T:
    """
    Extract the single item from a container of one item.

    This is used to access individual boards without needing their serial number.

    :param container: A mapping of connected boards of a type
    :raises RuntimeError: If there is not exactly one of this type of board connected
    :return: _description_
    """
    length = len(container)

    if length == 1:
        return list(container.values())[0]
    elif length == 0:
        raise RuntimeError('No boards of this type found')
    else:
        raise RuntimeError(f'expected only one to be connected, but found {length}')


def obtain_lock(lock_port: int = 10653) -> socket.socket:
    """
    Bind to a port to claim it and prevent another process using it.

    We use this to prevent multiple robot instances running on the same machine,
    as they would conflict with each other.

    :param lock_port: The port to bind to, defaults to 10653 to be compatible with sr-robot3
    :raises OSError: If the port failed to bind, indicating another robot instance is running
    :return: The bound socket
    """
    lock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # We bind to a port to claim it and prevent another process using it
    try:
        lock.bind(("localhost", lock_port))
    except OSError:
        raise OSError('Unable to obtain lock, Is another robot instance already running?')

    return lock


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

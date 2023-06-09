from __future__ import annotations

import logging
import socket
from abc import abstractmethod
from typing import Any, Mapping, NamedTuple, TypeVar

from serial.tools.list_ports_common import ListPortInfo

T = TypeVar('T')
logger = logging.getLogger(__name__)


class BoardIdentity(NamedTuple):
    manufacturer: str = ""
    board_type: str = ""
    asset_tag: str = ""
    sw_version: str = ""


class Board:
    @abstractmethod
    def identify(self) -> BoardIdentity:
        pass


def map_to_int(
        x: float,
        in_min: float,
        in_max: float,
        out_min: int,
        out_max: int,
) -> int:
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
    value = (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
    return round(value, precision)


def singular(container: Mapping[str, T]) -> T:
    length = len(container)

    if length == 1:
        return list(container.values())[0]
    elif length == 0:
        raise RuntimeError('No boards of this type found')
    else:
        raise RuntimeError(f'expected only one to be connected, but found {length}')


def obtain_lock(lock_port: int = 10653) -> socket.socket:
    lock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # We bind to a port to claim it and prevent another process using it
    try:
        lock.bind(("localhost", lock_port))
    except OSError:
        raise OSError('Unable to obtain lock, Is another robot instance already running')

    return lock


def float_bounds_check(value: Any, min_val: float, max_val: float, err_msg: str) -> float:
    try:
        new_val = float(value)
    except Exception as e:
        raise TypeError(err_msg) from e

    if (new_val < min_val) or (new_val > max_val):
        raise ValueError(err_msg)

    return new_val


def get_USB_identity(port: ListPortInfo) -> BoardIdentity:
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

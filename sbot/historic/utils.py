"""General utility functions and classes for the sbot package."""
from __future__ import annotations

import socket
from typing import Mapping, TypeVar

# Re-export all the internal utilities
from sbot.internal.utils import *  # noqa: F403

T = TypeVar('T')


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

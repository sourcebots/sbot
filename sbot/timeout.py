"""Functions for killing the robot after a certain amount of time."""
import logging
import os
import signal
import sys
from threading import Timer
from types import FrameType
from typing import Optional

logger = logging.getLogger(__name__)


def timeout_handler(signal_type: int, stack_frame: Optional[FrameType]) -> None:
    """
    Handle the timeout to kill the current process.

    This function is called when the timeout expires and will stop the robot's main process.
    In order for this to work, any threads that are created must be daemons.

    NOTE: This function is not called on Windows.

    :param signal_type: The sginal that triggered this handler
    :param stack_frame: The stack frame at the time of the signal
    """
    logger.info("Timeout expired: Game Over!")
    exit(0)


def win_timeout_handler() -> None:
    """
    Kill the main process on Windows.

    This function is called when the timeout expires and will stop the robot's main process.
    In order for this to work, any threads that are created must be daemons.

    NOTE: This function is only called on Windows.
    """
    logger.info("Timeout expired: Game Over!")
    os.kill(os.getpid(), signal.SIGTERM)


def kill_after_delay(timeout_seconds: int) -> None:
    """
    Kill the robot after a certain amount of time.

    Interrupts main process after the given delay.

    :param timeout_seconds: The number of seconds to wait before killing the robot
    """

    if sys.platform == "win32":
        # Windows doesn't have SIGALRM,
        # so we approximate its functionality using a delayed SIGTERM
        timer = Timer(timeout_seconds, win_timeout_handler)
        timer.start()
    else:
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout_seconds)
    logger.debug(f"Kill Signal Timeout set: {timeout_seconds}s")

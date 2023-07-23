"""Functions for killing the robot after a certain amount of time."""
import logging
import os
import platform
import signal
from threading import Timer
from types import FrameType
from typing import Optional

logger = logging.getLogger(__name__)


IS_LINUX = platform.system() == "Linux"

# `SIGALRM` will only exist on Linux
TERMINATING_SIGNAL = getattr(signal, "SIGALRM", signal.SIGTERM)


def raise_signal(signum: int) -> None:
    """
    Sends a signal to the current process.

    Similar to `signal.raise_signal`, however uses the main process's signal handler.

    :param signum: The signal to raise
    """
    os.kill(os.getpid(), signum)


def timeout_handler(signal_type: int, stack_frame: Optional[FrameType]) -> None:
    """
    Handle the timeout to kill the current process.

    This function is called when the timeout expires and will stop the robot's main process.
    In order for this to work, any threads that are created must be daemons.
    """
    print("Timeout expired: Game Over!")
    exit(0)


def kill_after_delay(timeout_seconds: int) -> None:
    """
    Kill the robot after a certain amount of time.

    Interrupts main process after the given delay.

    :param timeout_seconds: The number of seconds to wait before killing the robot
    """

    if IS_LINUX:
        signal.signal(TERMINATING_SIGNAL, timeout_handler)

    timer = Timer(timeout_seconds, lambda: raise_signal(TERMINATING_SIGNAL))

    logger.debug(f"Kill Signal Timeout set: {timeout_seconds}s")
    timer.start()

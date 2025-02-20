"""Functions for killing the robot after a certain amount of time."""
import atexit
import logging
import os
import signal
import sys
from threading import Timer
from types import FrameType
from typing import Optional

logger = logging.getLogger(__name__)

TIMEOUT_MESSAGE = "Timeout expired: Game Over!"
EXIT_ATTEMPTS = 0


def timeout_handler(signal_type: int, stack_frame: Optional[FrameType]) -> None:
    """
    Handle the timeout to kill the current process.

    This function is called when the timeout expires and will stop the robot's main process.
    In order for this to work, any threads that are created must be daemons.

    If the process doesn't terminate clearly (perhaps because the exception was caught),
    exit less cleanly.

    NOTE: This function is not called on Windows.

    :param signal_type: The sginal that triggered this handler
    :param stack_frame: The stack frame at the time of the signal
    """
    global EXIT_ATTEMPTS
    EXIT_ATTEMPTS += 1

    if sys.platform == "win32":
        raise AssertionError("This function should not be called on Windows")

    if EXIT_ATTEMPTS == 1:
        # Allow 2 seconds for the process to exit cleanly before killing it
        signal.alarm(2)
        logger.info(TIMEOUT_MESSAGE)
        # Exit cleanly
        exit(0)
    else:
        # The process didn't exit cleanly, so first call the cleanup handlers
        # and use an unhanded alarm to force python to exit with a core dump
        signal.signal(signal.SIGALRM, signal.SIG_DFL)
        signal.alarm(2)  # Allow 2 seconds for cleanup

        atexit._run_exitfuncs()  # noqa: SLF001
        exit(0)


def win_timeout_handler() -> None:
    """
    Kill the main process on Windows.

    This function is called when the timeout expires and will stop the robot's main process.
    In order for this to work, any threads that are created must be daemons.

    NOTE: This function is only called on Windows.
    """
    logger.info(TIMEOUT_MESSAGE)
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
        timer.daemon = True
        timer.start()
    else:
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout_seconds)
    logger.debug(f"Kill Signal Timeout set: {timeout_seconds}s")

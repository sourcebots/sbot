"""Functions for killing the robot after a certain amount of time."""
import logging
import signal
import sys
from types import FrameType

logger = logging.getLogger(__name__)

# TODO make this work on Windows


def timeout_handler(signal_type: signal.Signals, stack_frame: FrameType) -> None:
    """
    Handle the `SIGALRM` to kill the current process.

    This function is called when the timeout expires and will stop the robot's main process.
    In order for this to work, any threads that are created must be daemons.

    NOTE: This function is not called on Windows.

    :param signal_type: The sginal that triggered this handler
    :param stack_frame: The stack frame at the time of the signal
    :raises SystemExit: To stop the robot's execution after the timeout
    """
    raise SystemExit("Timeout expired: Game Over!")


def kill_after_delay(timeout_seconds: int) -> None:
    """
    Kill the robot after a certain amount of time.

    Interrupts main process after the given delay.

    NOTE: This functionality does not work on Windows,
    so the robot will not stop after the timeout.

    :param timeout_seconds: The number of seconds to wait before killing the robot
    """
    if sys.platform == "win32":
        logger.warning(
            "Game timeout is not supported on Windows. "
            "The code will not stop after the timeout.")
    else:
        logger.debug(f"Kill Signal Timeout set: {timeout_seconds}s")
        signal.signal(signal.SIGALRM, timeout_handler)  # type: ignore
        signal.alarm(timeout_seconds)

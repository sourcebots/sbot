"""Code to kill robot after certain amount of time."""
import logging
import sys
import signal
from types import FrameType

logger = logging.getLogger(__name__)

# TODO improve so will work on windows


def timeout_handler(signal_type: signal.Signals, stack_frame: FrameType) -> None:
    """Handle the `SIGALRM` to kill the current process."""
    raise SystemExit("Timeout expired: Game Over!")


def kill_after_delay(timeout_seconds: int) -> None:
    """Interrupts main process after the given delay."""
    if sys.platform == "win32":
        logger.warning(
            "Game timeout is not supported on Windows. "
            "The code will not stop after the timeout.")
    else:
        logger.debug(f"Kill Signal Timeout set: {timeout_seconds}s")
        signal.signal(signal.SIGALRM, timeout_handler)  # type: ignore
        signal.alarm(timeout_seconds)

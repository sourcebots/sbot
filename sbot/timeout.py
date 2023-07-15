"""Functions for killing the robot after a certain amount of time."""
import _thread
import logging
from threading import Timer

logger = logging.getLogger(__name__)


def timeout_handler() -> None:
    """
    Handle the timeout to kill the current process.

    This function is called when the timeout expires and will stop the robot's main process.
    In order for this to work, any threads that are created must be daemons.
    """
    logger.info("Timeout expired: Game Over!")
    _thread.interrupt_main()


def kill_after_delay(timeout_seconds: int) -> None:
    """
    Kill the robot after a certain amount of time.

    Interrupts main process after the given delay.

    :param timeout_seconds: The number of seconds to wait before killing the robot
    """
    timer = Timer(timeout_seconds, timeout_handler)
    logger.debug(f"Kill Signal Timeout set: {timeout_seconds}s")
    timer.start()

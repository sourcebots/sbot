"""
Top-level module for the robot API.

Contains instances of all the classes needed to interact with the robot hardware.
"""
import logging

from sbot._version import __version__
from sbot.future.board_manager import BoardManager
from sbot.future.overrides import get_overrides
from sbot.logging import setup_logging
from sbot.utils import ensure_atexit_on_term

from .arduinos import Arduino
from .comp import Comp
from .leds import Led
from .motors import Motor
from .power import Power
from .servos import Servo
from .utils import Utils
from .vision import Vision

logger = logging.getLogger(__name__)

# Ensure that the atexit handler is registered to clean up the boards on termination
ensure_atexit_on_term()

boards = BoardManager()
power = Power(boards)
motors = Motor(boards)
servos = Servo(boards)
arduino = Arduino(boards)
vision = Vision(boards)
leds = Led(boards)
comp = Comp()
utils = Utils(boards, comp)

# TODO lock?

overrides = get_overrides()

# Configure logging based on the environment variables
setup_logging(
    debug_logging=overrides.get('ENABLE_DEBUG_LOGGING', "0") != "0",
    trace_logging=overrides.get('ENABLE_TRACE_LOGGING', "0") != "0",
)

logger.info(f"SourceBots classless API v{__version__}")

# By default, load the boards and wait for the start button to be pressed.
if overrides.get('SKIP_WAIT_START', "0") == "0":
    utils.load_boards()
    utils.wait_start()

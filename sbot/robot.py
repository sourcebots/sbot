"""
Top-level module for the robot API.

Contains instances of all the classes needed to interact with the robot hardware.
"""
import logging

from ._arduinos import Arduino
from ._comp import Comp
from ._leds import Led
from ._motors import Motor
from ._power import Power
from ._servos import Servo
from ._utils import Utils
from ._version import __version__
from ._vision import Vision
from .internal.board_manager import BoardManager
from .internal.logging import setup_logging
from .internal.overrides import get_overrides
from .internal.utils import ensure_atexit_on_term

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

logger.info(f"SourceBots API v{__version__}")

# By default, load the boards and wait for the start button to be pressed.
if overrides.get('SKIP_WAIT_START', "0") == "0":
    utils.load_boards()
    utils.wait_start()

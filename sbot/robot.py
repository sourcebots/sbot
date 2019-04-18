"""SourceBots Robot Definition."""

import logging

from j5 import __version__, BaseRobot

__version__ = "0.1.0"

LOGGER = logging.getLogger(__name__)


class Robot(BaseRobot):
    """SourceBots robot."""

    def __init__(self, debug=False):
        if debug:
            LOGGER.setLevel(logging.DEBUG)
        LOGGER.info(f"SourceBots API v{__version__}")
        LOGGER.debug(f"j5 Version: {__version__}")

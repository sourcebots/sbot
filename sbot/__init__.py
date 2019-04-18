"""SourceBots API."""

from .robot import __version__, Robot
from .logging import logger_setup

logger_setup()

__all__ = ["__version__", "Robot"]

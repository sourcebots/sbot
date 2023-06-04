from .logging import logger_setup
from .motor_board import BRAKE, COAST
from .robot import Robot

logger_setup()

__all__ = [
    'BRAKE',
    'COAST',
    'Robot',
]

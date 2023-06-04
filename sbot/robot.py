import logging

from .motor_board import MotorBoard
from .servo_board import ServoBoard

logger = logging.getLogger(__name__)


def setup_logging(trace_logging):
    root_logger = logging.getLogger()
    root_logger.addHandler(logging.StreamHandler())
    if trace_logging:
        root_logger.setLevel(logging.TRACE)
    else:
        root_logger.setLevel(logging.INFO)


class Robot:
    def __init__(self, trace_logging=False):
        setup_logging(trace_logging)
        self.m = MotorBoard._get_supported_boards()
        self.s = ServoBoard._get_supported_boards()

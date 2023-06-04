import logging
from time import sleep

from april_vision.examples.camera import setup_cameras

from . import game_specific, metadata
from .exceptions import MetadataKeyError, MetadataNotReadyError
from .motor_board import MotorBoard
from .power_board import PowerBoard
from .servo_board import ServoBoard
from .utils import obtain_lock, singular

logger = logging.getLogger(__name__)


def setup_logging(trace_logging):
    logformat = '%(asctime)s [%(levelname)s] : %(module)s : %(message)s'
    formatter = logging.Formatter(fmt=logformat)
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    if trace_logging:
        root_logger.setLevel(logging.TRACE)
    else:
        root_logger.setLevel(logging.INFO)


class Robot:
    def __init__(self, trace_logging=False):
        self._lock = obtain_lock()
        self._metadata = None

        setup_logging(trace_logging)

        self._init_power_board()
        self._init_aux_boards()
        self._init_camera()

    def _init_power_board(self):
        power_boards = PowerBoard._get_supported_boards()
        self._power_board = singular(power_boards)
        self._power_board.outputs.power_on()
        # TODO delay for boards to power up ???

    def _init_aux_boards(self):
        self._motor_boards = MotorBoard._get_supported_boards()
        self._servo_boards = ServoBoard._get_supported_boards()

    def _init_camera(self):
        self._cameras = setup_cameras(game_specific.MARKER_SIZES)

    @property
    def power_boards(self):
        return self._power_boards

    @property
    def power_board(self):
        return singular(self._power_boards)

    @property
    def motor_boards(self):
        return self._motor_boards

    @property
    def motor_board(self):
        return singular(self._motor_boards)

    @property
    def servo_boards(self):
        return self._servo_boards

    @property
    def servo_board(self):
        return singular(self._servo_boards)

    @property
    def camera(self):
        return singular(self._cameras)

    def sleep(self, secs):
        sleep(secs)

    @property
    def metadata(self):
        if self._metadata is None:
            raise MetadataNotReadyError()
        else:
            return self._metadata

    @property
    def zone(self):
        try:
            return self.metadata['zone']
        except KeyError:
            raise MetadataKeyError('zone') from None

    @property
    def is_competition(self):
        try:
            return self.metadata['is_competition']
        except KeyError:
            raise MetadataKeyError('is_competition') from None

    def wait_start(self):
        # TODO make this work
        # TODO get the metadata at this point
        pass


# TODO double check logging handlers
# TODO bounds checks and type checks
# TODO error handling
# TODO add all the logging
# TODO repr/str on all the things

# TODO game timeout
# TODO loading metadata
# TODO immutable dict
# TODO arduino support
# TODO add atexits for boards

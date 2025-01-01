from .arduinos import Arduino
from .comp import Comp
from .motors import Motor
from .power import Power
from .servos import Servo
from .utils import BoardManager, Utils

boards = BoardManager()
power = Power(boards)
motor = Motor(boards)
servo = Servo(boards)
arduino = Arduino(boards)
comp = Comp()
utils = Utils(boards, comp)

# TODO load overrides
# TODO overrides ENABLE_TRACE_LOGGING, ENABLE_DEBUG_LOGGING

if True:  # TODO override SKIP_WAIT_START
    boards.load_boards()
    utils.wait_start()

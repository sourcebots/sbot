#!/usr/bin/env python3
"""
Power board test

To run this with an SRv4 Power Board connect power resistors to all the 12V
outputs and the 5V output. Size the resistors so that the total current with
all 12V outputs enabled is between 10A and 25A.

The test will:
- Test the current draw on each output with and without the output enabled
- Test the global current with multiple outputs enabled
- Enable and disable the run and error LEDs
- Detect the start button being pressed
- Play the buzzer

This assumes that the 5V output is the brain power output
"""
# Power board:
# - output switch (+5v)
# - output current sense (+5v)
# - global current sense
# - uvlo
# - buzzer
# - start button
# - leds
import logging

from sbot.power_board import PowerBoard
from sbot.robot import setup_logging
from sbot.utils import singular

HIGH_CURRENT_RESISTANCE = 4.7 / 2
LOW_CURRENT_RESISTANCE = 4.7
REGULATOR_RESISTANCE = 4.0

setup_logging()
logger = logging.getLogger("tester")

board = singular(PowerBoard._get_supported_boards())
board_identity = board.identify()

logger.info(
    f"Running power board test on board: {board_identity.asset_tag} "
    f"running firmware version: {board_identity.sw_version}.")

input_voltage = board.battery_sensor.voltage()
assert 11.5 < input_voltage < 12.5, \
    f"Input voltage of {input_voltage:.3f}V is outside acceptable range."
# TODO calc expected currents using this voltage

# test 5v voltage
# test output current
# disable brain output
# test off current

# for output
#   test off current
#   enable output
#   test output current
#   test global current

# enable all low outputs
# test global current

# enable all outputs
# test global current

# fan?

# leds

# start button

# buzzer

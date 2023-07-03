#!/usr/bin/env python3
"""
Servo board test

To run this with an SRv4 Servo Board connect servos to all outputs.

The test will:
- Move all 12 servos
"""
import argparse
import csv
import logging
import os
import textwrap
from time import sleep

from sbot.power_board import PowerBoard, PowerOutputPosition
from sbot.robot import setup_logging
from sbot.servo_board import ServoBoard
from sbot.utils import singular

setup_logging(False, False)
logger = logging.getLogger("tester")


def test_board(output_writer):
    results = {}
    pb = singular(PowerBoard._get_supported_boards())
    pb.outputs[PowerOutputPosition.L1].is_enabled = True
    board = singular(ServoBoard._get_supported_boards())
    try:
        board_identity = board.identify()

        results['asset'] = board_identity.asset_tag
        results['sw_version'] = board_identity.sw_version
        logger.info(
            f"Running servo board test on board: {board_identity.asset_tag} "
            f"running firmware version: {board_identity.sw_version}.")

        board.reset()
        sleep(2)

        input_voltage = board.voltage
        # expected currents are calculated using this voltage
        logger.info(f"Detected input voltage {input_voltage:.3f}V")
        results['input_volt'] = input_voltage
        assert 5 < input_voltage < 6, \
            f"Input voltage of {input_voltage:.3f}V is outside acceptable range of 5.5V±0.5V."

        # move all servos
        for i in range(12):
            board.servos[i].position = -0.8
        sleep(0.5)
        for i in range(12):
            board.servos[i].position = 0.8
        sleep(0.5)
        for i in range(12):
            board.servos[i].position = -0.8
        sleep(0.5)
        for i in range(12):
            board.servos[i].position = 0

        move_result = input("Did the servos move [y/n]")
        results['servos_move'] = move_result
        assert move_result.lower() == 'y', "Reported that the servos didn't move."

        logger.info("Board passed")
    finally:
        if output_writer is not None:
            output_writer.writerow(results)

        board.reset()


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(__doc__))
    parser.add_argument('--log', default=None, help='A CSV file to save test results to.')
    args = parser.parse_args()
    if args.log:
        new_log = True
        if os.path.exists(args.log):
            new_log = False
        with open(args.log, 'a', newline='') as csvfile:
            fieldnames = ['first_name', 'last_name']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if new_log:
                writer.writeheader()
            test_board(writer)
    else:
        test_board(None)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Motor board test

To run this with an SRv4 Motor Board connect power resistors to the motor
outputs. Size the resistors so that the current with 100% duty cycle is
is between 2A and 8A.

The test will:
- Test the current draw on each motor in both directions at a few duty cycles
"""
import argparse
import csv
import logging
import os
import textwrap
from time import sleep

from sbot.logging import setup_logging
from sbot.motor_board import MotorBoard
from sbot.power_board import PowerBoard, PowerOutputPosition
from sbot.utils import singular

MOTOR_RESISTANCE = 4.7

setup_logging(False, False)
logger = logging.getLogger("tester")


def log_and_assert_bounds(results, key, value, name, unit, min, max):
    logger.info(f"Detected {name}: {value:.3f}{unit}")
    results[key] = value
    center = (min + max) / 2
    variance = (max - min) / 2
    assert min < value < max, (
        f"{name.capitalize()} of {value:.3f}{unit} is outside acceptable range of "
        f"{center:.2f}±{variance:.2f}{unit}.")


def log_and_assert(results, key, value, name, unit, nominal, tolerance, offset=0):
    logger.info(f"Detected {name}: {value:.3f}{unit}")
    results[key] = value
    min = nominal * (1 - tolerance) - offset
    max = nominal * (1 + tolerance) + offset
    assert min < value < max, (
        f"{name.capitalize()} of {value:.3f}{unit} is outside acceptable range of "
        f"{nominal:.2f}±{tolerance:.0%}{f'±{offset:.2f}{unit}' if offset != 0 else ''}.")


def test_board(output_writer, use_power_board):
    results = {}
    if use_power_board:
        pb = singular(PowerBoard._get_supported_boards())
        try:
            pb.outputs[PowerOutputPosition.L2].is_enabled = True
        except RuntimeError:
            logger.warning("Failed to enable L2 on power board, this may be the brain port.")
    board = singular(MotorBoard._get_supported_boards())
    try:
        results['passed'] = False  # default to failure
        board_identity = board.identify()

        results['asset'] = board_identity.asset_tag
        results['sw_version'] = board_identity.sw_version
        logger.info(
            f"Running motor board test on board: {board_identity.asset_tag} "
            f"running firmware version: {board_identity.sw_version}.")

        board.reset()
        sleep(0.5)

        # expected currents are calculated using this voltage
        input_voltage = board.status.input_voltage
        log_and_assert_bounds(
            results, 'input_volt', input_voltage, 'input voltage', 'V', 11.5, 12.5)

        for motor in range(2):
            logger.info(f"Testing motor {motor}")
            # test off current
            log_and_assert_bounds(
                results, f'motor_{motor}_off_current', board.motors[motor].current,
                f'motor {motor} off state current', 'A', -0.2, 0.2)

            for direction in (1, -1):
                for abs_power in range(100, 10, -20):
                    power = abs_power * direction
                    logger.info(f"Testing {power:.0f}% power")
                    board.motors[motor].power = power / 100
                    sleep(0.1)

                    expected_out_current = (
                        (input_voltage / MOTOR_RESISTANCE) * (abs_power / 100))
                    # test output current
                    log_and_assert(
                        results, f'motor_{motor}_{power}_current', board.motors[motor].current,
                        f"motor {motor}, {power:.0f}% power", 'A', expected_out_current,
                        0.1, 0.2)

        logger.info("Board passed")
        results['passed'] = True
    finally:
        if output_writer is not None:
            output_writer.writerow(results)
        board.reset()


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(__doc__))
    parser.add_argument(
        '-pb', '--use-power-board', action='store_true',
        help="Enable port L2 on a connected power board to supply 12V to the motor board")
    parser.add_argument('--log', default=None, help='A CSV file to save test results to.')
    args = parser.parse_args()
    if args.log:
        new_log = True
        if os.path.exists(args.log):
            new_log = False
        with open(args.log, 'a', newline='') as csvfile:
            fieldnames = [
                'asset', 'sw_version', 'passed', 'input_volt',
                'motor_0_off_current', 'motor_1_off_current',
            ] + [
                f'motor_{motor}_{power * direction:.0f}_current'
                for motor in range(2)
                for direction in (1, -1)
                for power in range(100, 10, -20)
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if new_log:
                writer.writeheader()
            test_board(writer, args.use_power_board)
    else:
        test_board(None, args.use_power_board)


if __name__ == '__main__':
    main()

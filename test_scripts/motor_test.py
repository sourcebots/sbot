#!/usr/bin/env python3
"""
Motor board test

To run this with an SRv4 Motor Board connect power resistors to the motor
outputs. Size the resistors so that the current with 100% duty cycle is
is between 2A and 8A.

The test will:
- Test the current draw on each motor in both directions at a few duty cycles
"""
import logging
from time import sleep

from sbot.motor_board import MotorBoard
from sbot.power_board import PowerBoard, PowerOutputPosition
from sbot.robot import setup_logging
from sbot.utils import singular

MOTOR_RESISTANCE = 4.7

setup_logging(False, False)
logger = logging.getLogger("tester")


def test_board():
    results = {}
    pb = singular(PowerBoard._get_supported_boards())
    pb.outputs[PowerOutputPosition.L2].is_enabled = True
    board = singular(MotorBoard._get_supported_boards())
    try:
        board_identity = board.identify()

        results['asset'] = board_identity.asset_tag
        results['sw_version'] = board_identity.sw_version
        logger.info(
            f"Running motor board test on board: {board_identity.asset_tag} "
            f"running firmware version: {board_identity.sw_version}.")

        board.reset()
        sleep(2)

        input_voltage = board.status()[1]
        # expected currents are calculated using this voltage
        logger.info(f"Detected input voltage {input_voltage:.3f}V")
        results['input_volt'] = input_voltage
        assert 11.5 < input_voltage < 12.5, \
            f"Input voltage of {input_voltage:.3f}V is outside acceptable range of 12V±0.5V."

        for motor in range(2):
            logger.info(f"Testing motor {motor}")
            # test off current
            output_off_current = board.motors[motor].current
            logger.info(
                f"Detected motor {motor} off state current: {output_off_current:.3f}A")
            results[f'motor_{motor}_off_current'] = output_off_current
            assert -0.2 < output_off_current < 0.2, (
                f"Motor {motor} off state current of {output_off_current:.3f}A is outside "
                "acceptable range of -0.2-0.2A.")

            for direction in (1, -1):
                for abs_power in range(100, 10, -10):
                    power = abs_power * direction
                    test_step = f"motor {motor}, {power:.0f}% power"
                    logger.info(f"Testing {power:.0f}% power")
                    board.motors[motor].power = power / 100
                    sleep(0.25)

                    expected_out_current = (input_voltage / MOTOR_RESISTANCE) * (abs_power / 100)  # noqa
                    min_current_bound = (expected_out_current * 0.9) - 0.2
                    max_current_bound = (expected_out_current * 1.1) + 0.1

                    # test output current
                    output_current = board.motors[motor].current
                    logger.info(f"Detected {test_step}, current: {output_current:.3f}A")
                    results[f'motor_{motor}_{power}_current'] = output_current
                    assert min_current_bound < output_current < max_current_bound, (
                        f"{test_step}, current of {output_current:.3f}A is outside "
                        f"acceptable range of {expected_out_current:.3f}A±10%-0.2A/+0.1A.")

        logger.info("Board passed")
    finally:
        print(results)
        board.reset()


def main():
    test_board()


if __name__ == '__main__':
    main()

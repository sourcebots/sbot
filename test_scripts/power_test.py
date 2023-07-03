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
import argparse
import atexit
import csv
import logging
import os
import textwrap
from time import sleep

from sbot.logging import setup_logging
from sbot.power_board import PowerBoard, PowerOutputPosition
from sbot.utils import singular

HIGH_CURRENT_RESISTANCE = 4.7 / 2
LOW_CURRENT_RESISTANCE = 4.7
REGULATOR_RESISTANCE = 4.0

setup_logging(False, False)
logger = logging.getLogger("tester")


def test_board(output_writer):
    results = {}
    board = singular(PowerBoard._get_supported_boards())
    try:
        # Unregister the cleanup as we have our own
        atexit.unregister(board._cleanup)
        board_identity = board.identify()

        results['asset'] = board_identity.asset_tag
        results['sw_version'] = board_identity.sw_version
        logger.info(
            f"Running power board test on board: {board_identity.asset_tag} "
            f"running firmware version: {board_identity.sw_version}.")

        board.reset()
        sleep(2)

        input_voltage = board.battery_sensor.voltage
        # expected currents are calculated using this voltage
        logger.info(f"Detected input voltage {input_voltage:.3f}V")
        results['input_volt'] = input_voltage
        assert 11.5 < input_voltage < 12.5, \
            f"Input voltage of {input_voltage:.3f}V is outside acceptable range of 12V±0.5V."

        reg_voltage = board.status.regulator_voltage
        logger.info(f"Detected regulator voltage: {reg_voltage:.3f}V")
        results['reg_volt'] = reg_voltage
        assert 4.5 < reg_voltage < 5.5, \
            f"Regulator voltage of {reg_voltage:.3f}V is outside acceptable range of 5V±0.5V."

        reg_current = board.outputs[PowerOutputPosition.FIVE_VOLT].current
        logger.info(f"Detected regulator current: {reg_current:.3f}A")
        results['reg_current'] = reg_current
        expected_reg_current = reg_voltage / REGULATOR_RESISTANCE
        assert (expected_reg_current * 0.9) < reg_current < (expected_reg_current * 1.1), (
            f"Regulator current of {reg_current:.3f}A is outside acceptable "
            f"range of {expected_reg_current:.3f}A±10%.")

        # disable brain output
        board._serial.write('*SYS:BRAIN:SET:0')
        sleep(1)

        # test off current
        reg_off_current = board.outputs[PowerOutputPosition.FIVE_VOLT].current
        logger.info(f"Detected regulator off state current: {reg_off_current:.3f}A")
        results['reg_off_current'] = reg_off_current
        assert -0.2 < reg_off_current < 0.2, (
            f"Regulator off state current of {reg_off_current:.3f}A is outside "
            "acceptable range of -0.2-0.2A.")

        for output in PowerOutputPosition:
            if output == PowerOutputPosition.FIVE_VOLT:
                # skip brain output
                continue

            # test off current
            output_off_current = board.outputs[output].current
            logger.info(
                f"Detected output {output.name} off state current: {output_off_current:.3f}A")
            results[f'out_{output.name}_off_current'] = output_off_current
            assert -0.2 < output_off_current < 0.2, (
                f"Output off state current of {output_off_current:.3f}A is outside "
                "acceptable range of -0.2-0.2A.")

            # enable output
            board.outputs[output].is_enabled = True
            sleep(1)

            if output in {PowerOutputPosition.H0, PowerOutputPosition.H1}:
                expected_out_current = input_voltage / HIGH_CURRENT_RESISTANCE
            else:
                expected_out_current = input_voltage / LOW_CURRENT_RESISTANCE

            min_current_bound = (expected_out_current * 0.9)
            max_current_bound = (expected_out_current * 1.1)

            # test output current
            output_current = board.outputs[output].current
            logger.info(f"Detected output {output.name} current: {output_current:.3f}A")
            results[f'out_{output.name}_current'] = output_current
            assert min_current_bound < output_current < max_current_bound, (
                f"Output current of {output_current:.3f}A is outside "
                f"acceptable range of {expected_out_current:.3f}A±10%.")

            # test global current
            output_global_current = board.battery_sensor.current
            logger.info(f"Detected global output current: {output_global_current:.3f}A")
            results[f'out_{output.name}_global_current'] = output_global_current
            assert min_current_bound < output_global_current < max_current_bound, (
                f"Output current of {output_global_current:.3f}A is outside "
                f"acceptable range of {expected_out_current:.3f}A±10%.")

            # disable output
            board.outputs[output].is_enabled = False
            sleep(1)

        # enable all low outputs
        logger.info("Enabling all low current outputs")
        board.outputs[PowerOutputPosition.L0].is_enabled = True
        board.outputs[PowerOutputPosition.L1].is_enabled = True
        board.outputs[PowerOutputPosition.L2].is_enabled = True
        board.outputs[PowerOutputPosition.L3].is_enabled = True
        sleep(1)

        expected_out_current = 4 * input_voltage / LOW_CURRENT_RESISTANCE
        min_current_bound = (expected_out_current * 0.9)
        max_current_bound = (expected_out_current * 1.1)

        # test global current
        output_global_current = board.battery_sensor.current
        logger.info(f"Detected global output current: {output_global_current:.3f}A")
        results['out_low_global_current'] = output_global_current
        assert min_current_bound < output_global_current < max_current_bound, (
            f"Output current of {output_global_current:.3f}A is outside "
            f"acceptable range of {expected_out_current:.3f}A±10%.")
        board.outputs.power_off()

        # enable all outputs
        logger.info("Enabling all outputs")
        board.outputs[PowerOutputPosition.H0].is_enabled = True
        board.outputs[PowerOutputPosition.H1].is_enabled = True
        board.outputs[PowerOutputPosition.L0].is_enabled = True
        board.outputs[PowerOutputPosition.L1].is_enabled = True
        board.outputs[PowerOutputPosition.L2].is_enabled = True
        board.outputs[PowerOutputPosition.L3].is_enabled = True
        sleep(1)

        expected_out_current = (
            2 * input_voltage / HIGH_CURRENT_RESISTANCE
            + 4 * input_voltage / LOW_CURRENT_RESISTANCE
        )
        min_current_bound = (expected_out_current * 0.9)
        max_current_bound = (expected_out_current * 1.1)

        # test global current
        output_global_current = board.battery_sensor.current
        logger.info(f"Detected global output current: {output_global_current:.3f}A")
        results['out_global_current'] = output_global_current
        assert min_current_bound < output_global_current < max_current_bound, (
            f"Output current of {output_global_current:.3f}A is outside "
            f"acceptable range of {expected_out_current:.3f}A±10%.")
        board.outputs.power_off()

        # fan?
        # force the fan to run
        board._serial.write('*SYS:FAN:SET:1')
        fan_result = input("Is the fan running? [y/n]")
        results['fan'] = fan_result
        assert fan_result.lower() == 'y', "Reported that the fan didn't work."
        board._serial.write('*SYS:FAN:SET:0')

        # leds
        board._run_led.on()
        run_result = input("Is the run led green? [y/n]")
        results['run_led'] = run_result
        assert run_result.lower() == 'y', "Reported that the run LED didn't work."

        board._run_led.off()
        board._error_led.on()
        err_led_result = input("Is the error led red? [y/n]")
        results['err_led'] = err_led_result
        assert err_led_result.lower() == 'y', "Reported that the error LED didn't work."

        board._error_led.off()

        # buzzer
        board.piezo.buzz(0.5, 1000)
        buzz_result = input("Did the buzzer buzz? [y/n]")
        results['buzzer'] = buzz_result
        assert buzz_result.lower() == 'y', "Reported that the buzzer didn't buzz."

        # start button
        board._start_button()
        logger.info("Please press the start button")
        while not board._start_button():
            sleep(0.1)
        results['start_btn'] = "y"

        logger.info("Board passed")
    finally:
        if output_writer is not None:
            output_writer.writerow(results)

        # Disable all outputs
        board.reset()
        board._serial.write('*SYS:BRAIN:SET:0')


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
            fieldnames = [
                'asset', 'sw_version', 'input_volt',
                'reg_volt', 'reg_current', 'reg_off_current',
                'out_H0_off_current', 'out_H0_current', 'out_H0_global_current',
                'out_H1_off_current', 'out_H1_current', 'out_H1_global_current',
                'out_L0_off_current', 'out_L0_current', 'out_L0_global_current',
                'out_L1_off_current', 'out_L1_current', 'out_L1_global_current',
                'out_L2_off_current', 'out_L2_current', 'out_L2_global_current',
                'out_L3_off_current', 'out_L3_current', 'out_L3_global_current',
                'out_low_global_current', 'out_global_current',
                'fan', 'run_led', 'err_led', 'buzzer', 'start_btn']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if new_log:
                writer.writeheader()
            test_board(writer)
    else:
        test_board(None)


if __name__ == '__main__':
    main()

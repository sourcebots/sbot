#!/usr/bin/env python3
"""
Power board test

To run this with an SRv4 Power Board connect power resistors to all the 12V
outputs and the 5V output. Size the resistors so that the total current with
all 12V outputs enabled is between 10A and 25A.

The test will:
- Enable and disable the run and error LEDs
- Play the buzzer
- Detect the start button being pressed
- Test the current draw on each output with and without the output enabled
- Test the global current with multiple outputs enabled

The brain output is set by the BRAIN_OUTPUT constant below.
"""
import argparse
import atexit
import csv
import logging
import os
import textwrap
import threading
from time import sleep

from sbot.logging import setup_logging
from sbot.power_board import PowerBoard, PowerOutputPosition
from sbot.utils import singular

BRAIN_OUTPUT = PowerOutputPosition.FIVE_VOLT
OUTPUT_RESISTANCE = [
    4.7 / 2,  # H0
    4.7 / 2,  # H1
    4.7,  # L0
    4.7,  # L1
    4.7,  # L2
    4.7,  # L3
    4.0,  # 5V
]

setup_logging(False, False)
logger = logging.getLogger("tester")
run_led_thread = True


def log_and_assert_bounds(results, key, value, name, unit, min, max):
    logger.info(f"Detected {name}: {value:.3f}{unit}")
    results[key] = value
    center = (min + max) / 2
    variance = (max - min) / 2
    assert min < value < max, (
        f"{name.capitalize()} of {value:.3f}{unit} is outside acceptable range of "
        f"{center:.2f}±{variance:.2f}{unit}.")


def log_and_assert(results, key, value, name, unit, nominal, tolerance):
    logger.info(f"Detected {name}: {value:.3f}{unit}")
    results[key] = value
    min = nominal * (1 - tolerance)
    max = nominal * (1 + tolerance)
    assert min < value < max, (
        f"{name.capitalize()} of {value:.3f}{unit} is outside acceptable range of "
        f"{nominal:.2f}±{tolerance:.0%}.")


def test_output(board, results, output, input_voltage):
    if output == PowerOutputPosition.FIVE_VOLT:
        test_regulator(board, results)
        return

    log_and_assert_bounds(  # test off current
        results, f'out_{output.name}_off_current', board.outputs[output].current,
        f'output {output.name} off state current', 'A', -0.2, 0.2)

    # enable output
    if BRAIN_OUTPUT == output:
        board._serial.write('*SYS:BRAIN:SET:1')
    else:
        board.outputs[output].is_enabled = True
    sleep(0.5)

    expected_out_current = input_voltage / OUTPUT_RESISTANCE[output]
    log_and_assert(  # test output current
        results, f'out_{output.name}_current', board.outputs[output].current,
        f'output {output.name} current', 'A', expected_out_current, 0.1)
    log_and_assert(  # test global current
        results, f'out_{output.name}_global_current', board.battery_sensor.current,
        'global output current', 'A', expected_out_current, 0.1)

    # disable output
    if BRAIN_OUTPUT == output:
        board._serial.write('*SYS:BRAIN:SET:0')
    else:
        board.outputs[output].is_enabled = False
    sleep(0.5)


def test_regulator(board, results):
    # test off current
    log_and_assert_bounds(
        results, 'reg_off_current', board.outputs[PowerOutputPosition.FIVE_VOLT].current,
        'regulator off state current', 'A', -0.2, 0.2)

    # enable output
    if BRAIN_OUTPUT == PowerOutputPosition.FIVE_VOLT:
        board._serial.write('*SYS:BRAIN:SET:1')
    else:
        board.outputs[PowerOutputPosition.FIVE_VOLT].is_enabled = True
    sleep(0.5)

    reg_voltage = board.status.regulator_voltage
    log_and_assert_bounds(
        results, 'reg_volt', reg_voltage, 'regulator voltage', 'V', 4.5, 5.5)

    expected_reg_current = reg_voltage / OUTPUT_RESISTANCE[PowerOutputPosition.FIVE_VOLT]
    log_and_assert(
        results, 'reg_current', board.outputs[PowerOutputPosition.FIVE_VOLT].current,
        'regulator current', 'A', expected_reg_current, 0.1)

    # disable output
    if BRAIN_OUTPUT == PowerOutputPosition.FIVE_VOLT:
        board._serial.write('*SYS:BRAIN:SET:0')
    else:
        board.outputs[PowerOutputPosition.FIVE_VOLT].is_enabled = False
    sleep(0.5)


def led_flash(board):
    """Flash the run and error LEDs out of phase"""
    while run_led_thread:
        board._run_led.on()
        board._error_led.off()
        sleep(0.5)
        board._run_led.off()
        board._error_led.on()
        sleep(0.5)


def test_board(output_writer, test_uvlo):
    global run_led_thread
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
        # disable brain output
        board._serial.write('*SYS:BRAIN:SET:0')
        sleep(0.5)

        # expected currents are calculated using this voltage
        input_voltage = board.battery_sensor.voltage
        log_and_assert_bounds(
            results, 'input_volt', input_voltage, 'input voltage', 'V', 11.5, 12.5)

        # fan
        # force the fan to run
        board._serial.write('*SYS:FAN:SET:1')
        fan_result = input("Is the fan running? [y/n]")
        results['fan'] = fan_result
        assert fan_result.lower() == 'y', "Reported that the fan didn't work."
        board._serial.write('*SYS:FAN:SET:0')

        # buzzer
        board.piezo.buzz(0.5, 1000)
        buzz_result = input("Did the buzzer buzz? [y/n]")
        results['buzzer'] = buzz_result
        assert buzz_result.lower() == 'y', "Reported that the buzzer didn't buzz."

        # leds
        run_led_thread = True
        flash_thread = threading.Thread(target=led_flash, args=(board,), daemon=True)
        flash_thread.start()
        led_result = input("Are the LEDs flashing? [y/n]")
        results['leds'] = led_result
        assert led_result.lower() == 'y', "Reported that the LEDs didn't work."

        run_led_thread = False
        flash_thread.join()
        board._run_led.off()
        board._error_led.off()

        # start button
        board._start_button()
        logger.info("Please press the start button")
        while not board._start_button():
            sleep(0.1)
        results['start_btn'] = "y"

        for output in PowerOutputPosition:
            test_output(board, results, output, input_voltage)

        total_expected_current = 0
        for output in PowerOutputPosition:
            if output == BRAIN_OUTPUT:
                continue
            total_expected_current += input_voltage / OUTPUT_RESISTANCE[output]
            if total_expected_current > 25.0:
                # stop before we hit the current limit
                break

            board.outputs[output].is_enabled = True
            log_and_assert(
                results, f'sum_out_{output.name}_current', board.battery_sensor.current,
                f'output current up to {output.name}', 'A', total_expected_current, 0.1)
            sleep(0.5)

        # disable all outputs
        board.outputs.power_off()

        if test_uvlo:
            # TODO test UVLO
            pass

        logger.info("Board passed")
        results['passed'] = True
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
    parser.add_argument('--test-uvlo', action='store_true', help='Test the UVLO circuit.')
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
                'sum_out_H0_current', 'sum_out_H1_current', 'sum_out_L0_current',
                'sum_out_L1_current', 'sum_out_L2_current', 'sum_out_L3_current',
                'sum_out_FIVE_VOLT_current',
                'fan', 'leds', 'buzzer', 'start_btn', 'passed']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if new_log:
                writer.writeheader()
            test_board(writer, args.test_uvlo)
    else:
        test_board(None, args.test_uvlo)


if __name__ == '__main__':
    main()

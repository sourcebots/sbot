"""
Test that the arduino board can be created and used.

This test uses a mock serial wrapper to simulate the connection to the arduino board.
"""
from __future__ import annotations

from typing import NamedTuple, Generator

import pytest

from sbot._arduinos import AnalogPin, Arduino, GPIOPinMode
from sbot.internal.utils import BoardIdentity

from .conftest import MockSerialWrapper, setup_mock_board_manager


class MockArduino(NamedTuple):
    """A mock arduino board."""

    serial_wrapper: MockSerialWrapper
    arduino_board: Arduino


@pytest.fixture
def arduino_serial() -> Generator[MockArduino, None, None]:
    serial_wrapper = MockSerialWrapper([])
    serial_wrapper.set_identity(BoardIdentity(asset_tag='TEST123'))
    board_manager = setup_mock_board_manager()
    arduino_board = Arduino(board_manager)
    assert arduino_board._identifier == 'arduino'
    board_manager.preload_boards(board_manager)
    board_manager.boards[arduino_board._identifier] = {'TEST123': serial_wrapper}

    yield MockArduino(serial_wrapper, arduino_board)

    # Test that we made all the expected calls
    assert serial_wrapper.request_index == len(serial_wrapper.responses)


def test_arduino_ultrasound(arduino_serial: MockArduino) -> None:
    """
    Test the arduino ultrasound method.

    This test uses the mock serial wrapper to simulate the arduino.
    """
    arduino = arduino_serial.arduino_board
    arduino_serial.serial_wrapper._add_responses([
        ("ULTRASOUND:5:6:MEASURE?", "2345"),
    ])

    # Test that the ultrasound method returns the correct value
    assert arduino.measure_ultrasound_distance(5, 6) == 2345

    # Test that the ultrasound method checks the pin numbers are valid
    with pytest.raises(ValueError):
        arduino.measure_ultrasound_distance(0, 1)
    with pytest.raises(ValueError):
        arduino.measure_ultrasound_distance(2, 25)
    with pytest.raises(ValueError):
        arduino.measure_ultrasound_distance(25, 2)


def test_arduino_pins(arduino_serial: MockArduino) -> None:
    """
    Test the arduino pins properties and methods.

    This test uses the mock serial wrapper to simulate the arduino.
    """
    arduino = arduino_serial.arduino_board
    arduino_serial.serial_wrapper._add_responses([
        # ("PIN:2:MODE:GET?", "OUTPUT"),
        # ("PIN:10:MODE:GET?", "INPUT_PULLUP"),
        # ("PIN:14:MODE:GET?", "INPUT"),
        ("PIN:2:MODE:SET:OUTPUT", "ACK"),
        ("PIN:10:MODE:SET:INPUT_PULLUP", "ACK"),
        ("PIN:14:MODE:SET:INPUT", "ACK"),
        # PIN:<n>:ANALOG:GET?
    ])

    # Test that we can get the mode of a pin
    # assert arduino.pins[2].mode == GPIOPinMode.OUTPUT
    # assert arduino.pins[10].mode == GPIOPinMode.INPUT_PULLUP
    # assert arduino.pins[AnalogPin.A0].mode == GPIOPinMode.INPUT

    with pytest.raises(IOError):
        arduino.set_pin_mode(2, 1)

    # Test that we can set the mode of a pin
    arduino.set_pin_mode(2, GPIOPinMode.OUTPUT)
    arduino.set_pin_mode(10, GPIOPinMode.INPUT_PULLUP)
    arduino.set_pin_mode(AnalogPin.A0, GPIOPinMode.INPUT)

    # Test that we can get the digital value of a pin
    arduino_serial.serial_wrapper._add_responses([
        ("PIN:2:DIGITAL:GET?", "1"),
        ("PIN:10:DIGITAL:GET?", "0"),
        ("PIN:14:DIGITAL:GET?", "1"),
    ])
    assert arduino.digital_read(2) is True
    assert arduino.digital_read(10) is False
    assert arduino.digital_read(AnalogPin.A0) is True

    # Test that we can set the digital value of a pin
    arduino_serial.serial_wrapper._add_responses([
        ("PIN:2:DIGITAL:SET:1", "ACK"),
        ("PIN:2:DIGITAL:SET:0", "ACK"),
    ])
    arduino.digital_write(2, True)
    arduino.digital_write(2, False)

    # Test that we can get the analog value of a pin
    arduino_serial.serial_wrapper._add_responses([
        ("PIN:14:ANALOG:GET?", "1000"),
    ])
    with pytest.raises(IOError, match=r"Pin does not support analog read"):
        arduino.analog_read(10)
    # 4.888 = round((5 / 1023) * 1000, 3)
    assert arduino.analog_read(AnalogPin.A0) == 4.888


def test_invalid_properties(arduino_serial: MockArduino) -> None:
    """
    Test that settng invalid properties raise an AttributeError.
    """
    arduino_board = arduino_serial.arduino_board

    with pytest.raises(AttributeError):
        arduino_board.invalid_property = 1

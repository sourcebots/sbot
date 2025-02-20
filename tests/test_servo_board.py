"""
Test that the servo board can be created and used.

This test uses a mock serial wrapper to simulate the connection to the servo board.
"""
from __future__ import annotations

from typing import NamedTuple, Generator

import pytest

from sbot._servos import Servo
from sbot.internal.utils import BoardIdentity

from .conftest import MockSerialWrapper, setup_mock_board_manager


class MockServoBoard(NamedTuple):
    """A mock servo board."""

    serial_wrapper: MockSerialWrapper
    servo_board: Servo


@pytest.fixture
def servoboard_serial() -> Generator[MockServoBoard, None, None]:
    serial_wrapper = MockSerialWrapper([])
    serial_wrapper.set_identity(BoardIdentity(asset_tag='TEST123'))
    board_manager = setup_mock_board_manager()
    servo_board = Servo(board_manager)
    assert servo_board._identifier == 'servo'
    board_manager.preload_boards(board_manager)
    board_manager.boards[servo_board._identifier] = {'TEST123': serial_wrapper}
    board_manager.populate_outputs()

    yield MockServoBoard(serial_wrapper, servo_board)

    # Test that we made all the expected calls
    assert serial_wrapper.request_index == len(serial_wrapper.responses)


def test_servo_board(servoboard_serial: MockServoBoard) -> None:
    """
    Test that the servo board functionality works.

    This test uses the mock serial wrapper to simulate the servo board.
    """
    servo_board = servoboard_serial.servo_board
    servoboard_serial.serial_wrapper._add_responses([
        ("*STATUS?", "1:0"),
        ("*RESET", "ACK"),
        ("SERVO:I?", "1234"),
        ("SERVO:V?", "5432"),
    ])

    # Test that we can get the servo board status
    assert servo_board.status(0) == (True, False)

    # Test that we can reset the servo board
    servo_board.reset()

    # Test that we can get the servo board servo current
    assert servo_board.get_current(0) == 1.234

    # Test that we can get the servo board servo voltage
    assert servo_board.get_voltage(0) == 5.432


def test_servo_board_servos(servoboard_serial: MockServoBoard) -> None:
    """
    Test that the servo board servo functionality works.
    """
    servo_board = servoboard_serial.servo_board
    servoboard_serial.serial_wrapper._add_responses([
        ("SERVO:0:SET:1050", "ACK"),
        ("SERVO:1:SET:1500", "ACK"),
        ("SERVO:0:SET:1000", "ACK"),
        ("SERVO:1:SET:1000", "ACK"),
        ("SERVO:0:SET:1100", "ACK"),
        ("SERVO:1:SET:2000", "ACK"),
        ("SERVO:0:GET?", "1025"),
        ("SERVO:1:GET?", "1750"),
        ("SERVO:0:DISABLE", "ACK"),
        ("SERVO:0:GET?", "0"),
    ])
    # Test that we can set the duty cycle limits
    servo_board.set_duty_limits(0, 1000, 1100)
    servo_board.set_duty_limits(1, 1000, 2000)

    # Test that we can get the duty cycle limits
    assert servo_board.get_duty_limits(0) == (1000, 1100)

    # Test that we can set the servo duty cycle
    servo_board.set_position(0, 0)
    servo_board.set_position(1, 0)

    servo_board.set_position(0, -1.0)
    servo_board.set_position(1, -1.0)
    servo_board.set_position(0, 1.0)
    servo_board.set_position(1, 1.0)

    # Test that we can get the servo duty cycle
    assert servo_board.get_position(0) == -0.5
    assert servo_board.get_position(1) == 0.5

    # Test that we can disable the servo
    servo_board.disable(0)
    assert servo_board.get_position(0) is None


def test_servo_board_bounds_checking(servoboard_serial: MockServoBoard) -> None:
    """
    Test that handling of out of bounds values is correct.
    """
    servo_board = servoboard_serial.servo_board
    # Invalid input values should be caught before sending to the motor board
    # so no serial messages are expected

    # invalid servo number
    with pytest.raises(ValueError):
        servo_board.set_position(20, 0)

    # invalid servo number type
    with pytest.raises(TypeError):
        servo_board.set_position('a', 0)
    with pytest.raises(TypeError):
        servo_board.set_position(0.1, 0)
    with pytest.raises(TypeError):
        servo_board.set_position(None, 0)

    # invalid servo value
    with pytest.raises(ValueError):
        servo_board.set_position(0, -1.1)
    with pytest.raises(ValueError):
        servo_board.set_position(0, 1.1)
    with pytest.raises(ValueError):
        servo_board.set_position(0, -100)

    # invalid servo value type
    with pytest.raises(TypeError):
        servo_board.set_position(0, 'a')
    with pytest.raises(TypeError):
        servo_board.set_position(0, {})

    # duty cycle limits
    with pytest.raises(ValueError):
        servo_board.set_duty_limits(0, 100, 1000)
    with pytest.raises(ValueError):
        servo_board.set_duty_limits(0, 1000, 10000)

    # duty cycle limits type
    with pytest.raises(TypeError):
        servo_board.set_duty_limits(0, 'a', 1000)
    with pytest.raises(TypeError):
        servo_board.set_duty_limits(0, 1000, 'a')
    with pytest.raises(TypeError):
        servo_board.set_duty_limits(0, 1000, None)
    with pytest.raises(TypeError):
        servo_board.set_duty_limits(0, None, 1000)
    with pytest.raises(TypeError):
        servo_board.set_duty_limits(0, 1000, 1000.1)


def test_invalid_properties(servoboard_serial: MockServoBoard) -> None:
    """
    Test that settng invalid properties raise an AttributeError.
    """
    servo_board = servoboard_serial.servo_board

    with pytest.raises(AttributeError):
        servo_board.invalid_property = 1

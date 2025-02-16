"""
Test that the motor board can be created and used.

This test uses a mock serial wrapper to simulate the connection to the motor board.
"""
from __future__ import annotations

from typing import NamedTuple, Generator

import pytest

from sbot._motors import Motor, MotorPower
from sbot.internal.utils import BoardIdentity

from .conftest import MockSerialWrapper, setup_mock_board_manager


class MockMotorBoard(NamedTuple):
    """A mock motor board."""

    serial_wrapper: MockSerialWrapper
    motor_board: Motor


@pytest.fixture
def motorboard_serial() -> Generator[MockMotorBoard, None, None]:
    serial_wrapper = MockSerialWrapper([])
    serial_wrapper.set_identity(BoardIdentity(asset_tag='TEST123'))
    board_manager = setup_mock_board_manager()
    motor_board = Motor(board_manager)
    assert motor_board._identifier == 'motor'
    board_manager.preload_boards(board_manager)
    board_manager.boards[motor_board._identifier] = {'TEST123': serial_wrapper}
    board_manager.populate_outputs()

    yield MockMotorBoard(serial_wrapper, motor_board)

    # Test that we made all the expected calls
    assert serial_wrapper.request_index == len(serial_wrapper.responses)


def test_motor_board(motorboard_serial: MockMotorBoard) -> None:
    """
    Test the general functionality of the motor board.

    This test uses the mock serial wrapper to simulate the motor board.
    """
    motorboard = motorboard_serial.motor_board
    serial_wrapper = motorboard_serial.serial_wrapper
    serial_wrapper._add_responses([
        ("*STATUS?", "0,1:5432"),
        ("*STATUS?", "0,1:5432"),
        ("*STATUS?", "0,1:5432"),
        ("*RESET", "ACK"),
    ])

    # Test that we can get the motor board status
    assert motorboard.status(0).input_voltage == 5.432
    assert motorboard.in_fault(0) is False
    assert motorboard.in_fault(1) is True

    # Test that we can reset the motor board
    motorboard.reset()


def test_motor_board_motors(motorboard_serial: MockMotorBoard) -> None:
    """
    Test the motor board motor functionality.
    """
    motorboard = motorboard_serial.motor_board
    serial_wrapper = motorboard_serial.serial_wrapper
    serial_wrapper._add_responses([
        ("MOT:0:SET:500", "ACK"),
        ("MOT:1:SET:512", "ACK"),
        ("MOT:0:DISABLE", "ACK"),
        ("MOT:1:DISABLE", "ACK"),
        ("MOT:0:SET:0", "ACK"),
        ("MOT:1:SET:0", "ACK"),
        ("MOT:0:GET?", "1:123"),
        ("MOT:1:GET?", "1:456"),
        ("MOT:0:GET?", "0:100"),
        ("MOT:1:GET?", "0:0"),
        ("MOT:0:I?", "1234"),
        ("MOT:1:I?", "12345"),
    ])

    # Test that we can set the motor power
    motorboard.set_power(0, 0.5)
    motorboard.set_power(1, 0.5123)

    # Test that we can disable the motors
    motorboard.set_power(0, MotorPower.COAST)
    motorboard.set_power(1, MotorPower.COAST)

    # Test setting the power to BRAKE
    motorboard.set_power(0, MotorPower.BRAKE)
    motorboard.set_power(1, MotorPower.BRAKE)

    # Test that we can get the motor power
    assert motorboard.get_power(0) == 0.123
    assert motorboard.get_power(1) == 0.456

    # Test that we can get the motor enabled state
    assert motorboard.get_power(0) == MotorPower.COAST
    assert motorboard.get_power(1) == MotorPower.COAST

    # Test that we can get the motor current
    assert motorboard.get_motor_current(0) == 1.234
    assert motorboard.get_motor_current(1) == 12.345


def test_motor_board_bounds_check(motorboard_serial: MockMotorBoard) -> None:
    """
    Test that handling of out of bounds values is correct.
    """
    motorboard = motorboard_serial.motor_board
    # Invalid input values should be caught before sending to the motor board
    # so no serial messages are expected

    # Test that we handle invalid output numbers correctly
    with pytest.raises(ValueError):
        motorboard.set_power(2, 0.5)

    # Test that we handle invalid output number types correctly
    with pytest.raises(TypeError):
        motorboard.set_power('a', 0.5)
    with pytest.raises(TypeError):
        motorboard.set_power(0.5, 0.5)
    with pytest.raises(TypeError):
        motorboard.set_power(None, 0.5)

    # Test that we handle invalid power values correctly
    with pytest.raises(ValueError):
        motorboard.set_power(0, -1.2)
    with pytest.raises(ValueError):
        motorboard.set_power(0, 1.2)
    with pytest.raises(ValueError):
        motorboard.set_power(0, 100)

    # Test that we handle invalid power value types correctly
    with pytest.raises(TypeError):
        motorboard.set_power(0, 'a')
    with pytest.raises(TypeError):
        motorboard.set_power(0, None)
    with pytest.raises(TypeError):
        motorboard.set_power(0, [0.5])


def test_invalid_properties(motorboard_serial: MockMotorBoard) -> None:
    """
    Test that settng invalid properties raise an AttributeError.
    """
    motor_board = motorboard_serial.motor_board

    with pytest.raises(AttributeError):
        motor_board.invalid_property = 1

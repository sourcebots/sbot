"""
Test that the motor board can be created and used.

This test uses a mock serial wrapper to simulate the connection to the motor board.
"""
from __future__ import annotations

import re
from typing import NamedTuple

import pytest

from sbot.exceptions import IncorrectBoardError
from sbot.motor_board import MotorBoard, MotorPower
from sbot.utils import singular

from .conftest import MockAtExit, MockSerialWrapper


class MockMotorBoard(NamedTuple):
    """A mock motor board."""

    serial_wrapper: MockSerialWrapper
    motor_board: MotorBoard


@pytest.fixture
def motorboard_serial(monkeypatch) -> None:
    serial_wrapper = MockSerialWrapper([
        ("*IDN?", "Student Robotics:MCv4B:TEST123:4.4"),  # Called by MotorBoard.__init__
    ])
    mock_atexit = MockAtExit()
    monkeypatch.setattr('sbot.motor_board.atexit', mock_atexit)
    monkeypatch.setattr('sbot.motor_board.SerialWrapper', serial_wrapper)
    motor_board = MotorBoard('test://')

    assert motor_board._cleanup in mock_atexit._callbacks

    yield MockMotorBoard(serial_wrapper, motor_board)

    # Test that we made all the expected calls
    assert serial_wrapper.request_index == len(serial_wrapper.responses)


def test_motor_board_identify(motorboard_serial: MockMotorBoard) -> None:
    """
    Test that we can create a motor board with a mock serial wrapper.

    Uses the identify method to test that the mock serial wrapper is working.
    """
    serial_wrapper = motorboard_serial.serial_wrapper
    serial_wrapper._add_responses([
        ("*IDN?", "Student Robotics:MCv4B:TEST456:4.4"),
    ])
    motor_board = motorboard_serial.motor_board

    # Test that the port was correctly passed to the mock serial wrapper init
    assert serial_wrapper._port == 'test://'

    # Test that the identity is correctly set from the first *IDN? response
    assert motor_board._identity.board_type == "MCv4B"
    assert motor_board._identity.asset_tag == "TEST123"

    # Test identify returns a fresh identity
    assert motor_board.identify().asset_tag == "TEST456"


def test_motor_board(motorboard_serial: MockMotorBoard) -> None:
    """
    Test the general functionality of the motor board.

    This test uses the mock serial wrapper to simulate the motor board.
    """
    motorboard = motorboard_serial.motor_board
    serial_wrapper = motorboard_serial.serial_wrapper
    serial_wrapper._add_responses([
        ("*IDN?", "Student Robotics:MCv4B:TEST456:4.4"),
        ("*STATUS?", "0,1:5432"),
        ("*STATUS?", "0,1:5432"),
        ("*STATUS?", "0,1:5432"),
        ("*RESET", "ACK"),
    ])

    # Test that we can get the motor board version
    assert motorboard.identify().sw_version == "4.4"

    # Test that we can get the motor board status
    assert motorboard.status.input_voltage == 5.432
    assert motorboard.motors[0].in_fault is False
    assert motorboard.motors[1].in_fault is True

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
    motorboard.motors[0].power = 0.5
    motorboard.motors[1].power = 0.5123

    # Test that we can disable the motors
    motorboard.motors[0].power = MotorPower.COAST
    motorboard.motors[1].power = MotorPower.COAST

    # Test setting the power to BRAKE
    motorboard.motors[0].power = MotorPower.BRAKE
    motorboard.motors[1].power = MotorPower.BRAKE

    # Test that we can get the motor power
    assert motorboard.motors[0].power == 0.123
    assert motorboard.motors[1].power == 0.456

    # Test that we can get the motor enabled state
    assert motorboard.motors[0].power == MotorPower.COAST
    assert motorboard.motors[1].power == MotorPower.COAST

    # Test that we can get the motor current
    assert motorboard.motors[0].current == 1.234
    assert motorboard.motors[1].current == 12.345


def test_motor_board_bounds_check(motorboard_serial: MockMotorBoard) -> None:
    """
    Test that handling of out of bounds values is correct.
    """
    motorboard = motorboard_serial.motor_board
    # Invalid input values should be caught before sending to the motor board
    # so no serial messages are expected

    # Test that we handle invalid output numbers correctly
    with pytest.raises(IndexError):
        motorboard.motors[2].power = 0.5

    # Test that we handle invalid output number types correctly
    with pytest.raises(TypeError):
        motorboard.motors['a'].power = 0.5
    with pytest.raises(TypeError):
        motorboard.motors[0.5].power = 0.5
    with pytest.raises(TypeError):
        motorboard.motors[None].power = 0.5

    # Test that we handle invalid power values correctly
    with pytest.raises(ValueError):
        motorboard.motors[0].power = -1.2
    with pytest.raises(ValueError):
        motorboard.motors[0].power = 1.2
    with pytest.raises(ValueError):
        motorboard.motors[0].power = 100

    # Test that we handle invalid power value types correctly
    with pytest.raises(TypeError):
        motorboard.motors[0].power = 'a'
    with pytest.raises(TypeError):
        motorboard.motors[0].power = None
    with pytest.raises(TypeError):
        motorboard.motors[0].power = [0.5]


def test_motor_board_cleanup(motorboard_serial: MockMotorBoard) -> None:
    """
    Test that the motor board cleanup method works.
    """
    motor_board = motorboard_serial.motor_board
    motorboard_serial.serial_wrapper._add_responses([
        ("*RESET", "ACK"),
    ])

    # Test that the cleanup method calls the reset method
    motor_board._cleanup()


def test_invalid_properties(motorboard_serial: MockMotorBoard) -> None:
    """
    Test that settng invalid properties raise an AttributeError.
    """
    motor_board = motorboard_serial.motor_board

    with pytest.raises(AttributeError):
        motor_board.invalid_property = 1

    with pytest.raises(AttributeError):
        motor_board.motors.invalid_property = 1

    with pytest.raises(AttributeError):
        motor_board.motors[0].invalid_property = 1


def test_motor_board_discovery(monkeypatch) -> None:
    """
    Test that discovery finds motor boards from USB serial ports.

    Test that different USB pid/vid combinations are ignored.
    """
    class ListPortInfo(NamedTuple):
        """A mock serial port info."""
        device: str
        manufacturer: str
        product: str
        serial_number: str
        vid: int
        pid: int

    def mock_comports() -> list[ListPortInfo]:
        ports = [
            ListPortInfo(
                device='test://1',
                manufacturer='Student Robotics',
                product='MCv4B',
                serial_number='TEST123',
                vid=0x0403,
                pid=0x6001,
            ),
            ListPortInfo(  # A motor board with a different pid/vid
                device='test://3',
                manufacturer='Other',
                product='MCv4B',
                serial_number='OTHER',
                vid=0x1234,
                pid=0x5678,
            ),
            ListPortInfo(  # An unrelated device
                device='test://5',
                manufacturer='Student Robotics',
                product='OTHER',
                serial_number='TESTABC',
                vid=0x0403,
                pid=0x6001,
            ),
        ]
        return ports

    serial_wrapper = MockSerialWrapper([
        ("*IDN?", "Student Robotics:MCv4B:TEST123:4.4"),  # USB discovered board
        ("*IDN?", "Student Robotics:OTHER:TESTABC:4.4"),  # USB invalid board
        ("*IDN?", "Student Robotics:MCv4B:TEST456:4.4"),  # Manually added board
        ("*IDN?", "Student Robotics:OTHER:TESTABC:4.4"),  # Manual invalid board
    ])
    # mock atexit so we don't end up registering the cleanup method
    monkeypatch.setattr('sbot.motor_board.atexit', MockAtExit())
    monkeypatch.setattr('sbot.motor_board.SerialWrapper', serial_wrapper)
    monkeypatch.setattr('sbot.motor_board.comports', mock_comports)

    motor_boards = MotorBoard._get_supported_boards(manual_boards=['test://2', 'test://4'])
    assert len(motor_boards) == 2
    assert {'TEST123', 'TEST456'} == set(motor_boards.keys())


def test_motor_board_invalid_identity(monkeypatch) -> None:
    """
    Test that we raise an error if the motor board returns an different board type.
    """
    serial_wrapper = MockSerialWrapper([
        ("*IDN?", "Student Robotics:TestBoard:TEST123:4.4"),  # Called by MotorBoard.__init__
    ])
    monkeypatch.setattr('sbot.motor_board.SerialWrapper', serial_wrapper)

    with pytest.raises(
        IncorrectBoardError,
        match=re.escape("Board returned type 'TestBoard', expected 'MCv4B'"),
    ):
        MotorBoard('test://')


@pytest.mark.hardware
def test_physical_motor_board_discovery() -> None:
    """Test that we can discover physical motor boards."""
    motor_boards = MotorBoard._get_supported_boards()
    assert len(motor_boards) == 1, "Did not find exactly one motor board."
    motor_board = singular(motor_boards)
    identity = motor_board.identify()
    assert identity.board_type == "MCv4B", "motor board is not the correct type."
    asset_tag = identity.asset_tag
    assert motor_board == motor_boards[asset_tag], \
        "Singular motor board is not the same as the one in the list of motor boards."

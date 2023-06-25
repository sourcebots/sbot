"""
Test that the servo board can be created and used.

This test uses a mock serial wrapper to simulate the connection to the servo board.
"""
from __future__ import annotations

import re
from typing import NamedTuple

import pytest

from sbot.exceptions import IncorrectBoardError
from sbot.servo_board import ServoBoard
from sbot.utils import singular

from .conftest import MockAtExit, MockSerialWrapper


class MockServoBoard(NamedTuple):
    """A mock servo board."""

    serial_wrapper: MockSerialWrapper
    servo_board: ServoBoard


@pytest.fixture
def servoboard_serial(monkeypatch) -> None:
    serial_wrapper = MockSerialWrapper([
        ("*IDN?", "Student Robotics:SBv4B:TEST123:4.3"),  # Called by ServoBoard.__init__
    ])
    mock_atexit = MockAtExit()
    monkeypatch.setattr('sbot.servo_board.atexit', mock_atexit)
    monkeypatch.setattr('sbot.servo_board.SerialWrapper', serial_wrapper)
    servo_board = ServoBoard('test://')

    assert servo_board._cleanup in mock_atexit._callbacks

    yield MockServoBoard(serial_wrapper, servo_board)

    # Test that we made all the expected calls
    assert serial_wrapper.request_index == len(serial_wrapper.responses)


def test_servo_board_identify(servoboard_serial: MockServoBoard) -> None:
    """
    Test that we can create a servo board with a mock serial wrapper.

    Uses the identify method to test that the mock serial wrapper is working.
    """
    serial_wrapper = servoboard_serial.serial_wrapper
    serial_wrapper._add_responses([
        ("*IDN?", "Student Robotics:SBv4B:TEST456:4.3"),
    ])
    servo_board = servoboard_serial.servo_board

    # Test that the port was correctly passed to the mock serial wrapper init
    assert serial_wrapper._port == 'test://'

    # Test that the identity is correctly set from the first *IDN? response
    assert servo_board._identity.board_type == "SBv4B"
    assert servo_board._identity.asset_tag == "TEST123"

    # Test identify returns a fresh identity
    assert servo_board.identify().asset_tag == "TEST456"


def test_servo_board(servoboard_serial: MockServoBoard) -> None:
    """
    Test that the servo board functionality works.

    This test uses the mock serial wrapper to simulate the servo board.
    """
    servo_board = servoboard_serial.servo_board
    servoboard_serial.serial_wrapper._add_responses([
        ("*IDN?", "Student Robotics:SBv4B:TEST123:4.3"),
        ("*STATUS?", "1:0"),
        ("*RESET", "ACK"),
        ("SERVO:I?", "1234"),
        ("SERVO:V?", "5432"),
    ])

    # Test that we can get the servo board version
    assert servo_board.identify().sw_version == "4.3"

    # Test that we can get the servo board status
    assert servo_board.status() == (True, False)

    # Test that we can reset the servo board
    servo_board.reset()

    # Test that we can get the servo board servo current
    assert servo_board.current == 1.234

    # Test that we can get the servo board servo voltage
    assert servo_board.voltage == 5.432


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
        ("SERVO:1:DISABLE", "ACK"),
        ("SERVO:1:GET?", "0"),
    ])
    # Test that we can set the duty cycle limits
    servo_board.servos[0].set_duty_limits(1000, 1100)

    # Test that we can get the duty cycle limits
    assert servo_board.servos[0].get_duty_limits() == (1000, 1100)

    # Test that we can set the servo duty cycle
    servo_board.servos[0].position = 0
    servo_board.servos[1].position = 0

    servo_board.servos[0].position = -1.0
    servo_board.servos[1].position = -1.0
    servo_board.servos[0].position = 1.0
    servo_board.servos[1].position = 1.0

    # Test that we can get the servo duty cycle
    assert servo_board.servos[0].position == -0.5
    assert servo_board.servos[1].position == 0.5

    # Test that we can disable the servo
    servo_board.servos[0].disable()
    assert servo_board.servos[0].position is None
    servo_board.servos[1].position = None
    assert servo_board.servos[1].position is None


def test_servo_board_bounds_checking(servoboard_serial: MockServoBoard) -> None:
    """
    Test that handling of out of bounds values is correct.
    """
    servo_board = servoboard_serial.servo_board
    # Invalid input values should be caught before sending to the motor board
    # so no serial messages are expected

    # invalid servo number
    with pytest.raises(IndexError):
        servo_board.servos[20].position = 0

    # invalid servo number type
    with pytest.raises(TypeError):
        servo_board.servos['a'].position = 0
    with pytest.raises(TypeError):
        servo_board.servos[0.1].position = 0
    with pytest.raises(TypeError):
        servo_board.servos[None].position = 0

    # invalid servo value
    with pytest.raises(ValueError):
        servo_board.servos[0].position = -1.1
    with pytest.raises(ValueError):
        servo_board.servos[0].position = 1.1
    with pytest.raises(ValueError):
        servo_board.servos[0].position = -100

    # invalid servo value type
    with pytest.raises(TypeError):
        servo_board.servos[0].position = 'a'
    with pytest.raises(TypeError):
        servo_board.servos[0].position = {}

    # duty cycle limits
    with pytest.raises(ValueError):
        servo_board.servos[0].set_duty_limits(100, 1000)
    with pytest.raises(ValueError):
        servo_board.servos[0].set_duty_limits(1000, 10000)

    # duty cycle limits type
    with pytest.raises(TypeError):
        servo_board.servos[0].set_duty_limits('a', 1000)
    with pytest.raises(TypeError):
        servo_board.servos[0].set_duty_limits(1000, 'a')
    with pytest.raises(TypeError):
        servo_board.servos[0].set_duty_limits(1000, None)
    with pytest.raises(TypeError):
        servo_board.servos[0].set_duty_limits(None, 1000)
    with pytest.raises(TypeError):
        servo_board.servos[0].set_duty_limits(1000, 1000.1)


def test_servo_board_cleanup(servoboard_serial: MockServoBoard) -> None:
    """
    Test that the servo board cleanup method works.
    """
    servo_board = servoboard_serial.servo_board
    servoboard_serial.serial_wrapper._add_responses([
        ("*RESET", "ACK"),
    ])

    # Test that the cleanup method calls the reset method
    servo_board._cleanup()


def test_invalid_properties(servoboard_serial: MockServoBoard) -> None:
    """
    Test that settng invalid properties raise an AttributeError.
    """
    servo_board = servoboard_serial.servo_board

    with pytest.raises(AttributeError):
        servo_board.invalid_property = 1

    with pytest.raises(AttributeError):
        servo_board.servos.invalid_property = 1

    with pytest.raises(AttributeError):
        servo_board.servos[0].invalid_property = 1


def test_servo_board_discovery(monkeypatch) -> None:
    """
    Test that discovery finds servo boards from USB serial ports.

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
                product='SBv4B',
                serial_number='TEST123',
                vid=0x1BDA,
                pid=0x0011,
            ),
            ListPortInfo(  # A servo board with a different pid/vid
                device='test://3',
                manufacturer='Other',
                product='SBv4B',
                serial_number='OTHER',
                vid=0x1234,
                pid=0x5678,
            ),
            ListPortInfo(  # An unrelated device
                device='test://5',
                manufacturer='Student Robotics',
                product='OTHER',
                serial_number='TESTABC',
                vid=0x1BDA,
                pid=0x0011,
            ),
        ]
        return ports

    serial_wrapper = MockSerialWrapper([
        ("*IDN?", "Student Robotics:SBv4B:TEST123:4.3"),  # USB discovered board
        ("*IDN?", "Student Robotics:OTHER:TESTABC:4.3"),  # USB invalid board
        ("*IDN?", "Student Robotics:SBv4B:TEST456:4.3"),  # Manually added board
        ("*IDN?", "Student Robotics:OTHER:TESTABC:4.3"),  # Manual invalid board
    ])
    # mock atexit so we don't end up registering the cleanup method
    monkeypatch.setattr('sbot.servo_board.atexit', MockAtExit())
    monkeypatch.setattr('sbot.servo_board.SerialWrapper', serial_wrapper)
    monkeypatch.setattr('sbot.servo_board.comports', mock_comports)

    servo_boards = ServoBoard._get_supported_boards(manual_boards=['test://2', 'test://4'])
    assert len(servo_boards) == 2
    assert {'TEST123', 'TEST456'} == set(servo_boards.keys())


def test_servo_board_invalid_identity(monkeypatch) -> None:
    """
    Test that we raise an error if the servo board returns an different board type.
    """
    serial_wrapper = MockSerialWrapper([
        ("*IDN?", "Student Robotics:TestBoard:TEST123:4.3"),  # Called by ServoBoard.__init__
    ])
    monkeypatch.setattr('sbot.servo_board.SerialWrapper', serial_wrapper)

    with pytest.raises(
        IncorrectBoardError,
        match=re.escape("Board returned type 'TestBoard', expected 'SBv4B'"),
    ):
        ServoBoard('test://')


@pytest.mark.hardware
def test_physical_servo_board_discovery() -> None:
    """Test that we can discover physical servo boards."""
    servo_boards = ServoBoard._get_supported_boards()
    assert len(servo_boards) == 1, "Did not find exactly one servo board."
    servo_board = singular(servo_boards)
    identity = servo_board.identify()
    assert identity.board_type == "SBv4B", "servo board is not the correct type."
    asset_tag = identity.asset_tag
    assert servo_board == servo_boards[asset_tag], \
        "Singular servo board is not the same as the one in the list of servo boards."

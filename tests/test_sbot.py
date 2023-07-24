"""Test that the module works."""
import logging
import socket

import pytest

from sbot import Robot
from sbot.exceptions import MetadataNotReadyError
from sbot.metadata import METADATA_ENV_VAR
from sbot.utils import BoardIdentity, obtain_lock

from .conftest import MockAtExit, MockSerialWrapper


def test_robot(monkeypatch, caplog) -> None:
    """Test that the Robot object can be created."""
    # monkey patch serial ports so we can test without hardware
    monkeypatch.setattr('sbot.power_board.SerialWrapper', MockSerialWrapper([
        ("*IDN?", "Student Robotics:PBv4B:POW123:4.4.1"),
        ("OUT:0:SET:1", "ACK"),
        ("OUT:1:SET:1", "ACK"),
        ("OUT:2:SET:1", "ACK"),
        ("OUT:3:SET:1", "ACK"),
        ("OUT:4:SET:1", "ACK"),
        ("OUT:5:SET:1", "ACK"),
        ("*IDN?", "Student Robotics:PBv4B:POW123:4.4.1"),
        ("BTN:START:GET?", "0:1"),
        ("NOTE:1760:100", "ACK"),  # Start up sound
        ("LED:RUN:SET:F", "ACK"),
        ("BTN:START:GET?", "0:0"),
        ("BTN:START:GET?", "0:1"),
        ("LED:RUN:SET:1", "ACK"),
    ]))
    monkeypatch.setattr('sbot.motor_board.SerialWrapper', MockSerialWrapper([
        ("*IDN?", "Student Robotics:MCv4B:MOT123:4.4"),
        ("*IDN?", "Student Robotics:MCv4B:MOT123:4.4"),
    ]))
    monkeypatch.setattr('sbot.servo_board.SerialWrapper', MockSerialWrapper([
        ("*IDN?", "Student Robotics:SBv4B:TEST123:4.3"),
        ("*IDN?", "Student Robotics:SBv4B:TEST123:4.3"),
    ]))
    monkeypatch.setattr('sbot.arduino.SerialWrapper', MockSerialWrapper([
        ("*IDN?", "Student Robotics:Arduino:X:2.0"),
        ("*IDN?", "Student Robotics:Arduino:X:2.0"),
    ]))

    # monkey patch atexit to avoid running cleanup code
    monkeypatch.setattr('sbot.power_board.atexit', MockAtExit())
    monkeypatch.setattr('sbot.motor_board.atexit', MockAtExit())
    monkeypatch.setattr('sbot.servo_board.atexit', MockAtExit())

    # Monkey patch serial comport lookup so only manual boards are found
    monkeypatch.setattr('sbot.power_board.comports', lambda: [])
    monkeypatch.setattr('sbot.motor_board.comports', lambda: [])
    monkeypatch.setattr('sbot.servo_board.comports', lambda: [])
    monkeypatch.setattr('sbot.arduino.comports', lambda: [])

    # Forget the camera
    monkeypatch.setattr('sbot.robot._setup_cameras', lambda *_: {})

    # Avoid searching filesystem for metadata
    monkeypatch.delenv(METADATA_ENV_VAR, raising=False)

    manual_boards = {
        'PBv4B': ['test://'],
        'SBv4B': ['test://'],
        'MCv4B': ['test://'],
        'Arduino': ['test://'],
    }
    # check logging
    caplog.clear()
    caplog.set_level(logging.INFO)

    # Test that we can obtain a lock before creating a robot object
    lock = obtain_lock()
    assert isinstance(lock, socket.socket)
    lock.close()  # release the lock

    # Test that we can create a robot object
    r = Robot(wait_for_start=False, manual_boards=manual_boards, debug=True)
    assert caplog.record_tuples[1:] == [
        # First line contains the version number
        ('sbot.robot', logging.INFO, 'Found PowerBoard, serial: POW123'),
        ('sbot.robot', logging.INFO, 'Found MotorBoard, serial: MOT123'),
        ('sbot.robot', logging.INFO, 'Found ServoBoard, serial: TEST123'),
        ('sbot.robot', logging.INFO, 'Found Arduino, serial: test://'),
    ]

    # Check we found all the boards
    assert r.power_board._identity == BoardIdentity(
        "Student Robotics", "PBv4B", "POW123", "4.4.1")

    assert r.motor_board._identity == BoardIdentity(
        "Student Robotics", "MCv4B", "MOT123", "4.4")

    assert r.servo_board._identity == BoardIdentity(
        "Student Robotics", "SBv4B", "TEST123", "4.3")

    assert r.arduino._identity == BoardIdentity(
        "Student Robotics", "Arduino", "test://", "2.0")

    # Check that a RuntimeError is raised if we have 0 instances of a board
    with pytest.raises(RuntimeError, match="No boards of this type found"):
        r.camera.identify()

    # Check that we can't obtain a lock when a robot object already exists
    with pytest.raises(
        OSError,
        match="Unable to obtain lock, Is another robot instance already running?"
    ):
        obtain_lock()

    # Check that an exception is raised if we try to access metadata before wait_start
    with pytest.raises(
        MetadataNotReadyError,
        match=".*can only be used after wait_start has been called"
    ):
        r.zone

    r.wait_start()

    assert r.zone == 0


@pytest.hookimpl(trylast=True)
@pytest.mark.hardware
def test_robot_discovery() -> None:
    """Test that we can discover all the boards when creating a Robot object."""
    from sbot import Robot
    robot = Robot(wait_for_start=False)

    # Test that we can access the singular boards
    power_asset_tag = robot.power_board.identify().asset_tag
    servo_asset_tag = robot.servo_board.identify().asset_tag
    motor_asset_tag = robot.motor_board.identify().asset_tag

    # Test that we can access the boards by asset tag
    assert robot.power_board == robot.boards[power_asset_tag]
    assert robot.servo_board == robot.boards[servo_asset_tag]
    assert robot.motor_board == robot.boards[motor_asset_tag]

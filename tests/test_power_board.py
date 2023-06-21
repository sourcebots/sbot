"""
Test that the power board can be created and used.

This test uses a mock serial wrapper to simulate the connection to the power board.
"""
import pytest

from sbot.power_board import PowerBoard
from sbot.utils import singular

from .conftest import MockSerialWrapper


def test_power_board_identify(monkeypatch) -> None:
    """
    Test that we can create a power board with a mock serial wrapper.

    Uses the identify method to test that the mock serial wrapper is working.
    """
    serial_wrapper = MockSerialWrapper([
        ("*IDN?", "Student Robotics:PBv4B:TEST123:4.4.1"),  # Called by PowerBoard.__init__
        ("*IDN?", "Student Robotics:PBv4B:TEST456:4.4.1"),
    ])
    monkeypatch.setattr('sbot.power_board.SerialWrapper', serial_wrapper)
    power_board = PowerBoard('test://')

    # Test that the port was correctly passed to the mock serial wrapper init
    assert serial_wrapper._port == 'test://'

    # Test that the identity is correctly set from the first *IDN? response
    assert power_board._identity.board_type == "PBv4B"
    assert power_board._identity.asset_tag == "TEST123"

    # Test identify returns a fresh identity
    assert power_board.identify().asset_tag == "TEST456"

    # Test that we made all the expected calls
    assert serial_wrapper.request_index == len(serial_wrapper.responses)


@pytest.mark.hardware
def test_power_board_discovery() -> None:
    """Test that we can discover physical power boards."""
    power_boards = PowerBoard._get_supported_boards()
    assert len(power_boards) == 1, "Did not find exactly one power board."
    power_board = singular(power_boards)
    identity = power_board.identify()
    assert identity.board_type == "PBv4B", "Power board is not the correct type."
    asset_tag = identity.asset_tag
    assert power_board == power_boards[asset_tag], \
        "Singular power board is not the same as the one in the list of power boards."

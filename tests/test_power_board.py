"""
Test that the power board can be created and used.

This test uses a mock serial wrapper to simulate the connection to the power board.
"""
from __future__ import annotations

import re
from typing import NamedTuple

import pytest

from sbot.exceptions import IncorrectBoardError
from sbot.power_board import Note, PowerBoard, PowerOutputPosition
from sbot.utils import singular

from .conftest import MockAtExit, MockSerialWrapper


class MockPowerBoard(NamedTuple):
    """A mock power board."""

    serial_wrapper: MockSerialWrapper
    power_board: PowerBoard


@pytest.fixture
def powerboard_serial(monkeypatch) -> None:
    serial_wrapper = MockSerialWrapper([
        ("*IDN?", "Student Robotics:PBv4B:TEST123:4.4.1"),  # Called by PowerBoard.__init__
    ])
    mock_atexit = MockAtExit()
    monkeypatch.setattr('sbot.power_board.atexit', mock_atexit)
    monkeypatch.setattr('sbot.power_board.SerialWrapper', serial_wrapper)
    power_board = PowerBoard('test://')

    assert power_board._cleanup in mock_atexit._callbacks

    yield MockPowerBoard(serial_wrapper, power_board)

    # Test that we made all the expected calls
    assert serial_wrapper.request_index == len(serial_wrapper.responses)


def test_power_board_identify(powerboard_serial: MockPowerBoard) -> None:
    """
    Test that we can create a power board with a mock serial wrapper.

    Uses the identify method to test that the mock serial wrapper is working.
    """
    serial_wrapper = powerboard_serial.serial_wrapper
    serial_wrapper._add_responses([
        ("*IDN?", "Student Robotics:PBv4B:TEST456:4.4.1"),
    ])
    power_board = powerboard_serial.power_board

    # Test that the port was correctly passed to the mock serial wrapper init
    assert serial_wrapper._port == 'test://'

    # Test that the identity is correctly set from the first *IDN? response
    assert power_board._identity.board_type == "PBv4B"
    assert power_board._identity.asset_tag == "TEST123"

    # Test identify returns a fresh identity
    assert power_board.identify().asset_tag == "TEST456"


def test_power_board(powerboard_serial: MockPowerBoard) -> None:
    """
    Test the general power board methods.
    """
    serial_wrapper = powerboard_serial.serial_wrapper
    serial_wrapper._add_responses([
        ("*IDN?", "Student Robotics:PBv4B:TEST456:4.4.1"),
        ("*IDN?", "Student Robotics:PBv4B:TEST456:4.4.1"),
        ("BATT:I?", "1234"),
        ("BATT:V?", "12450"),
        ("*STATUS?", "0,0,0,0,0,0,0:39:0:5234"),
        ("*STATUS?", "0,0,0,0,0,0,0:39:0:5234"),
        ("*STATUS?", "0,0,0,0,0,0,0:39:0:5234"),
        ("BTN:START:GET?", "0:1"),
        ("NOTE:1047:100", "ACK"),
        ("NOTE:261:234", "ACK"),
        ("*RESET", "ACK"),
    ])
    power_board = powerboard_serial.power_board

    # Test identify returns a fresh identity
    assert power_board.identify().asset_tag == "TEST456"

    # Test that we can get the power board version
    assert power_board.identify().sw_version == "4.4.1"

    # Test that we can get the power board total current
    assert power_board.battery_sensor.current == 1.234

    # Test that we can get the power board total voltage
    assert power_board.battery_sensor.voltage == 12.45

    # Test that we can get the power board temperature
    assert power_board.status.temperature == 39

    # Test that we can get the power board fan status
    assert power_board.status.fan_running is False

    # Test that we can get the power board regulator voltage
    assert power_board.status.regulator_voltage == 5.234

    # Test that we can get the power board start button status
    assert power_board._start_button() is True

    # Test that we can play a note using the Note class
    power_board.piezo.buzz(0.1, Note.C6)
    # And using a float
    power_board.piezo.buzz(0.2345, 261.63)

    # Test that we can reset the power board
    power_board.reset()


def test_power_board_leds(powerboard_serial: MockPowerBoard) -> None:
    """
    Test that the power board LEDs are correctly mapped and their methods work.
    """
    power_board = powerboard_serial.power_board
    powerboard_serial.serial_wrapper._add_responses([
        ("LED:RUN:SET:1", "ACK"),
        ("LED:RUN:SET:0", "ACK"),
        ("LED:RUN:SET:F", "ACK"),
        ("LED:ERR:SET:1", "ACK"),
        ("LED:ERR:SET:0", "ACK"),
        ("LED:ERR:SET:F", "ACK"),
    ])

    # Test that we can set the power board run LED
    power_board._run_led.on()
    power_board._run_led.off()
    power_board._run_led.flash()

    # Test that we can set the power board error LED
    power_board._error_led.on()
    power_board._error_led.off()
    power_board._error_led.flash()


def test_power_board_outputs(powerboard_serial: MockPowerBoard) -> None:
    """
    Test that the power board outputs are correctly mapped and their methods work.
    """
    power_board = powerboard_serial.power_board

    # Test that we can enable and disable the power board outputs
    powerboard_serial.serial_wrapper._add_responses([
        ("OUT:0:SET:1", "ACK"),
        ("OUT:1:SET:1", "ACK"),
        ("OUT:2:SET:1", "ACK"),
        ("OUT:3:SET:1", "ACK"),
        ("OUT:4:SET:1", "ACK"),
        ("OUT:5:SET:1", "ACK"),
        ("OUT:0:SET:0", "ACK"),
        ("OUT:1:SET:0", "ACK"),
        ("OUT:2:SET:0", "ACK"),
        ("OUT:3:SET:0", "ACK"),
        ("OUT:4:SET:0", "ACK"),
        ("OUT:5:SET:0", "ACK"),
    ])
    power_board.outputs.power_on()
    power_board.outputs.power_off()

    # Test that we can enable and disable the power board outputs individually
    powerboard_serial.serial_wrapper._add_responses([
        ("OUT:0:SET:1", "ACK"),
        ("OUT:0:SET:0", "ACK"),
        ("OUT:1:SET:1", "ACK"),
        ("OUT:1:SET:0", "ACK"),
        ("OUT:2:SET:1", "ACK"),
        ("OUT:2:SET:0", "ACK"),
        ("OUT:3:SET:1", "ACK"),
        ("OUT:3:SET:0", "ACK"),
        ("OUT:4:SET:1", "ACK"),
        ("OUT:4:SET:0", "ACK"),
        ("OUT:5:SET:1", "ACK"),
        ("OUT:5:SET:0", "ACK"),
    ])
    power_board.outputs[PowerOutputPosition.H0].is_enabled = True
    power_board.outputs[PowerOutputPosition.H0].is_enabled = False
    power_board.outputs[PowerOutputPosition.H1].is_enabled = True
    power_board.outputs[PowerOutputPosition.H1].is_enabled = False
    power_board.outputs[PowerOutputPosition.L0].is_enabled = True
    power_board.outputs[PowerOutputPosition.L0].is_enabled = False
    power_board.outputs[PowerOutputPosition.L1].is_enabled = True
    power_board.outputs[PowerOutputPosition.L1].is_enabled = False
    power_board.outputs[PowerOutputPosition.L2].is_enabled = True
    power_board.outputs[PowerOutputPosition.L2].is_enabled = False
    power_board.outputs[PowerOutputPosition.L3].is_enabled = True
    power_board.outputs[PowerOutputPosition.L3].is_enabled = False

    # Test that we can't enable or disable the 5V output
    with pytest.raises(RuntimeError, match=r"Brain output cannot be controlled.*"):
        power_board.outputs[PowerOutputPosition.FIVE_VOLT].is_enabled = True

    # Test that we can detect whether the power board outputs are enabled
    powerboard_serial.serial_wrapper._add_responses([
        ("OUT:0:GET?", "1"),
        ("OUT:1:GET?", "1"),
        ("OUT:2:GET?", "1"),
        ("OUT:3:GET?", "1"),
        ("OUT:4:GET?", "1"),
        ("OUT:5:GET?", "1"),
        ("OUT:6:GET?", "1"),
    ])
    assert power_board.outputs[PowerOutputPosition.H0].is_enabled is True
    assert power_board.outputs[PowerOutputPosition.H1].is_enabled is True
    assert power_board.outputs[PowerOutputPosition.L0].is_enabled is True
    assert power_board.outputs[PowerOutputPosition.L1].is_enabled is True
    assert power_board.outputs[PowerOutputPosition.L2].is_enabled is True
    assert power_board.outputs[PowerOutputPosition.L3].is_enabled is True
    assert power_board.outputs[PowerOutputPosition.FIVE_VOLT].is_enabled is True

    # Test that we can detect whether the power board outputs are overcurrent
    powerboard_serial.serial_wrapper._add_responses([
        ("*STATUS?", "0,1,0,1,0,1,0:39:0:5234"),
        ("*STATUS?", "0,1,0,1,0,1,0:39:0:5234"),
        ("*STATUS?", "0,1,0,1,0,1,0:39:0:5234"),
        ("*STATUS?", "0,1,0,1,0,1,0:39:0:5234"),
        ("*STATUS?", "0,1,0,1,0,1,0:39:0:5234"),
        ("*STATUS?", "0,1,0,1,0,1,0:39:0:5234"),
        ("*STATUS?", "0,1,0,1,0,1,0:39:0:5234"),
    ])
    assert power_board.outputs[PowerOutputPosition.H0].overcurrent is False
    assert power_board.outputs[PowerOutputPosition.H1].overcurrent is True
    assert power_board.outputs[PowerOutputPosition.L0].overcurrent is False
    assert power_board.outputs[PowerOutputPosition.L1].overcurrent is True
    assert power_board.outputs[PowerOutputPosition.L2].overcurrent is False
    assert power_board.outputs[PowerOutputPosition.L3].overcurrent is True
    assert power_board.outputs[PowerOutputPosition.FIVE_VOLT].overcurrent is False

    # Test that we can detect output current
    powerboard_serial.serial_wrapper._add_responses([
        ("OUT:0:I?", "1100"),
        ("OUT:1:I?", "1200"),
        ("OUT:2:I?", "1300"),
        ("OUT:3:I?", "1400"),
        ("OUT:4:I?", "1500"),
        ("OUT:5:I?", "1600"),
        ("OUT:6:I?", "1700"),
    ])
    assert power_board.outputs[PowerOutputPosition.H0].current == 1.1
    assert power_board.outputs[PowerOutputPosition.H1].current == 1.2
    assert power_board.outputs[PowerOutputPosition.L0].current == 1.3
    assert power_board.outputs[PowerOutputPosition.L1].current == 1.4
    assert power_board.outputs[PowerOutputPosition.L2].current == 1.5
    assert power_board.outputs[PowerOutputPosition.L3].current == 1.6
    assert power_board.outputs[PowerOutputPosition.FIVE_VOLT].current == 1.7


def test_power_board_cleanup(powerboard_serial: MockPowerBoard) -> None:
    """
    Test that the power board cleanup method works.
    """
    power_board = powerboard_serial.power_board
    powerboard_serial.serial_wrapper._add_responses([
        ("*RESET", "ACK"),
    ])

    # Test that the cleanup method calls the reset method
    power_board._cleanup()


def test_invalid_properties(powerboard_serial: MockPowerBoard) -> None:
    """
    Test that settng invalid properties raise an AttributeError.
    """
    power_board = powerboard_serial.power_board

    with pytest.raises(AttributeError):
        power_board.invalid_property = 1

    with pytest.raises(AttributeError):
        power_board.outputs.invalid_property = 1

    with pytest.raises(AttributeError):
        power_board.outputs[0].invalid_property = 1

    with pytest.raises(AttributeError):
        power_board.battery_sensor.invalid_property = 1

    with pytest.raises(AttributeError):
        power_board.piezo.invalid_property = 1


def test_power_board_bounds_check(powerboard_serial: MockPowerBoard) -> None:
    """
    Test that the power board bounds checking works.
    """
    power_board = powerboard_serial.power_board
    # Invalid input values should be caught before sending to the power board
    # so no serial messages are expected

    # Test that we can't enable or disable an invalid output number
    with pytest.raises(IndexError):
        power_board.outputs[10].is_enabled = True
    with pytest.raises(IndexError):
        power_board.outputs[7000].is_enabled = True

    # Test that we can't enable or disable an invalid output number type
    with pytest.raises(TypeError):
        power_board.outputs[None].is_enabled = True
    with pytest.raises(TypeError):
        power_board.outputs[1.5].is_enabled = True

    # Test that we can't buzz an invalid note frequency
    with pytest.raises(ValueError):
        power_board.piezo.buzz(0.1, -1)
    with pytest.raises(ValueError):
        power_board.piezo.buzz(0.1, 0)
    with pytest.raises(ValueError):
        power_board.piezo.buzz(0.1, 10001)

    # Test that we can't buzz an invalid note frequency type
    with pytest.raises(TypeError):
        power_board.piezo.buzz(0.1, None)
    with pytest.raises(TypeError):
        power_board.piezo.buzz(0.1, {})

    # Test that we can't buzz an invalid note duration
    with pytest.raises(ValueError):
        power_board.piezo.buzz(-1, 1000)
    with pytest.raises(ValueError):
        power_board.piezo.buzz(10**100, 1000)

    # Test that we can't buzz an invalid note duration type
    with pytest.raises(TypeError):
        power_board.piezo.buzz(None, 1000)
    with pytest.raises(TypeError):
        power_board.piezo.buzz({}, 1000)


def test_power_board_discovery(monkeypatch) -> None:
    """
    Test that discovery finds power boards from USB serial ports.

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
                product='PBv4B',
                serial_number='TEST123',
                vid=0x1BDA,
                pid=0x0010,
            ),
            ListPortInfo(  # A power board with a different pid/vid
                device='test://3',
                manufacturer='Other',
                product='PBv4B',
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
                pid=0x0010,
            ),
        ]
        return ports

    serial_wrapper = MockSerialWrapper([
        ("*IDN?", "Student Robotics:PBv4B:TEST123:4.4.1"),  # USB discovered board
        ("*IDN?", "Student Robotics:OTHER:TESTABC:4.4.1"),  # USB invalid board
        ("*IDN?", "Student Robotics:PBv4B:TEST456:4.4.1"),  # Manually added board
        ("*IDN?", "Student Robotics:OTHER:TESTABC:4.4.1"),  # Manual invalid board
    ])
    # mock atexit so we don't end up registering the cleanup method
    monkeypatch.setattr('sbot.power_board.atexit', MockAtExit())
    monkeypatch.setattr('sbot.power_board.SerialWrapper', serial_wrapper)
    monkeypatch.setattr('sbot.power_board.comports', mock_comports)

    power_boards = PowerBoard._get_supported_boards(manual_boards=['test://2', 'test://4'])
    assert len(power_boards) == 2
    assert {'TEST123', 'TEST456'} == set(power_boards.keys())


def test_power_board_invalid_identity(monkeypatch) -> None:
    """
    Test that we raise an error if the power board returns an different board type.
    """
    serial_wrapper = MockSerialWrapper([
        ("*IDN?", "Student Robotics:TestBoard:TEST123:4.4.1"),  # Called by PowerBoard.__init__
    ])
    monkeypatch.setattr('sbot.power_board.SerialWrapper', serial_wrapper)

    with pytest.raises(
        IncorrectBoardError,
        match=re.escape("Board returned type 'TestBoard', expected 'PBv4B'"),
    ):
        PowerBoard('test://')


@pytest.mark.hardware
def test_physical_power_board_discovery() -> None:
    """Test that we can discover physical power boards."""
    power_boards = PowerBoard._get_supported_boards()
    assert len(power_boards) == 1, "Did not find exactly one power board."
    power_board = singular(power_boards)
    identity = power_board.identify()
    assert identity.board_type == "PBv4B", "Power board is not the correct type."
    asset_tag = identity.asset_tag
    assert power_board == power_boards[asset_tag], \
        "Singular power board is not the same as the one in the list of power boards."

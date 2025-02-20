"""
Test that the power board can be created and used.

This test uses a mock serial wrapper to simulate the connection to the power board.
"""
from __future__ import annotations

from typing import NamedTuple, Generator

import pytest

from sbot.internal.utils import BoardIdentity
from sbot._power import Power, PowerOutputPosition, BatteryData
from sbot._utils import Utils, Note

from .conftest import MockSerialWrapper, setup_mock_board_manager


class MockPowerBoard(NamedTuple):
    """A mock power board."""

    serial_wrapper: MockSerialWrapper
    power_board: Power
    utils: Utils


@pytest.fixture
def powerboard_serial() -> Generator[MockPowerBoard, None, None]:
    serial_wrapper = MockSerialWrapper([])
    serial_wrapper.set_identity(BoardIdentity(asset_tag='TEST123'))
    board_manager = setup_mock_board_manager()
    power_board = Power(board_manager)
    utils = Utils(board_manager, None)  # Comp is not needed for this test
    assert power_board._identifier == 'power'
    board_manager.preload_boards(board_manager)
    board_manager.boards[power_board._identifier] = {'TEST123': serial_wrapper}
    board_manager.populate_outputs()

    yield MockPowerBoard(serial_wrapper, power_board, utils)

    # Test that we made all the expected calls
    assert serial_wrapper.request_index == len(serial_wrapper.responses)


def test_power_board(powerboard_serial: MockPowerBoard) -> None:
    """
    Test the general power board methods.
    """
    serial_wrapper = powerboard_serial.serial_wrapper
    serial_wrapper._add_responses([
        ("BATT:V?", "12450"),
        ("BATT:I?", "1234"),
        ("*STATUS?", "0,0,0,0,0,0,0:39:0:5234"),
        ("*STATUS?", "0,0,0,0,0,0,0:39:0:5234"),
        ("*STATUS?", "0,0,0,0,0,0,0:39:0:5234"),
        # ("BTN:START:GET?", "0:1"),
        ("*RESET", "ACK"),
    ])
    power_board = powerboard_serial.power_board

    # Test that we can get the power board total voltage & current
    assert power_board.get_battery_data() == BatteryData(voltage=12.45, current=1.234)

    # Test that we can get the power board temperature
    assert power_board.status().temperature == 39

    # Test that we can get the power board fan status
    assert power_board.status().fan_running is False

    # Test that we can get the power board regulator voltage
    assert power_board.status().regulator_voltage == 5.234

    # Test that we can reset the power board
    power_board.reset()


def test_power_board_outputs(powerboard_serial: MockPowerBoard) -> None:
    """
    Test that the power board outputs are correctly mapped and their methods work.
    """
    power_board = powerboard_serial.power_board

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
        ("OUT:5:SET:1", "ACK"),
        ("OUT:5:SET:0", "ACK"),
        ("OUT:6:SET:1", "ACK"),
        ("OUT:6:SET:0", "ACK"),
    ])
    power_board.set_output(PowerOutputPosition.H0, True)
    power_board.set_output(PowerOutputPosition.H0, False)
    power_board.set_output(PowerOutputPosition.H1, True)
    power_board.set_output(PowerOutputPosition.H1, False)
    power_board.set_output(PowerOutputPosition.L0, True)
    power_board.set_output(PowerOutputPosition.L0, False)
    power_board.set_output(PowerOutputPosition.L1, True)
    power_board.set_output(PowerOutputPosition.L1, False)
    power_board.set_output(PowerOutputPosition.L3, True)
    power_board.set_output(PowerOutputPosition.L3, False)
    power_board.set_output(PowerOutputPosition.FIVE_VOLT, True)
    power_board.set_output(PowerOutputPosition.FIVE_VOLT, False)

    # Test that we can't enable or disable the brain output
    with pytest.raises(RuntimeError, match=r"Brain output cannot be controlled.*"):
        power_board.set_output(PowerOutputPosition.L2, True)

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
    assert power_board.is_output_on(PowerOutputPosition.H0) is True
    assert power_board.is_output_on(PowerOutputPosition.H1) is True
    assert power_board.is_output_on(PowerOutputPosition.L0) is True
    assert power_board.is_output_on(PowerOutputPosition.L1) is True
    assert power_board.is_output_on(PowerOutputPosition.L2) is True
    assert power_board.is_output_on(PowerOutputPosition.L3) is True
    assert power_board.is_output_on(PowerOutputPosition.FIVE_VOLT) is True

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
    assert power_board.status().overcurrent[PowerOutputPosition.H0] is False
    assert power_board.status().overcurrent[PowerOutputPosition.H1] is True
    assert power_board.status().overcurrent[PowerOutputPosition.L0] is False
    assert power_board.status().overcurrent[PowerOutputPosition.L1] is True
    assert power_board.status().overcurrent[PowerOutputPosition.L2] is False
    assert power_board.status().overcurrent[PowerOutputPosition.L3] is True
    assert power_board.status().overcurrent[PowerOutputPosition.FIVE_VOLT] is False

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
    assert power_board.get_output_current(PowerOutputPosition.H0) == 1.1
    assert power_board.get_output_current(PowerOutputPosition.H1) == 1.2
    assert power_board.get_output_current(PowerOutputPosition.L0) == 1.3
    assert power_board.get_output_current(PowerOutputPosition.L1) == 1.4
    assert power_board.get_output_current(PowerOutputPosition.L2) == 1.5
    assert power_board.get_output_current(PowerOutputPosition.L3) == 1.6
    assert power_board.get_output_current(PowerOutputPosition.FIVE_VOLT) == 1.7


def test_invalid_properties(powerboard_serial: MockPowerBoard) -> None:
    """
    Test that settng invalid properties raise an AttributeError.
    """
    power_board = powerboard_serial.power_board

    with pytest.raises(AttributeError):
        power_board.invalid_property = 1


def test_power_board_bounds_check(powerboard_serial: MockPowerBoard) -> None:
    """
    Test that the power board bounds checking works.
    """
    power_board = powerboard_serial.power_board
    # Invalid input values should be caught before sending to the power board
    # so no serial messages are expected

    # Test that we can't enable or disable an invalid output number
    with pytest.raises(ValueError):
        power_board.set_output(10, True)
    with pytest.raises(ValueError):
        power_board.set_output(7000, True)

    # Test that we can't enable or disable an invalid output number type
    with pytest.raises(TypeError):
        power_board.set_output(None, True)
    with pytest.raises(TypeError):
        power_board.set_output(1.5, True)


def test_buzzer(powerboard_serial: MockPowerBoard) -> None:
    """
    Test that the power board buzzer works.
    """
    utils = powerboard_serial.utils
    powerboard_serial.serial_wrapper._add_responses([
        ("NOTE:1047:100", "ACK"),
        ("NOTE:261:234", "ACK"),
    ])


    # Test that we can play a note using the Note class
    utils.sound_buzzer(Note.C6, 0.1)
    # And using a float
    utils.sound_buzzer(261.63, 0.2345)

    # Test that we can't buzz an invalid note frequency
    with pytest.raises(ValueError):
        utils.sound_buzzer(-1, 0.1)
    with pytest.raises(ValueError):
        utils.sound_buzzer(0, 0.1)
    with pytest.raises(ValueError):
        utils.sound_buzzer(10001, 0.1)

    # Test that we can't buzz an invalid note frequency type
    with pytest.raises(TypeError):
        utils.sound_buzzer(None, 0.1)
    with pytest.raises(TypeError):
        utils.sound_buzzer({}, 0.1)

    # Test that we can't buzz an invalid note duration
    with pytest.raises(ValueError):
        utils.sound_buzzer(1000, -1)
    with pytest.raises(ValueError):
        utils.sound_buzzer(1000, 10**100)

    # Test that we can't buzz an invalid note duration type
    with pytest.raises(TypeError):
        utils.sound_buzzer(1000, None)
    with pytest.raises(TypeError):
        utils.sound_buzzer(1000, {})

"""Test that the module works."""
import pytest


def test_import() -> None:
    """Test that we can import the module."""
    import sbot  # noqa: F401


@pytest.hookimpl(trylast=True)
@pytest.mark.hardware
def test_robot_discovery() -> None:
    """Test that we can discover all the boards when creating a Robot object."""
    from sbot import Robot
    robot = Robot(wait_start=False)

    # Test that we can access the singular boards
    power_asset_tag = robot.power_board.identify().asset_tag
    servo_asset_tag = robot.servo_board.identify().asset_tag
    motor_asset_tag = robot.motor_board.identify().asset_tag

    # Test that we can access the boards by asset tag
    assert robot.power_board == robot.boards[power_asset_tag]
    assert robot.servo_board == robot.boards[servo_asset_tag]
    assert robot.motor_board == robot.boards[motor_asset_tag]

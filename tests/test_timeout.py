"""Test the timeout function."""
from time import sleep

import _thread

from sbot.timeout import kill_after_delay
from unittest.mock import Mock


def test_kill_after_delay(monkeypatch) -> None:
    """Test that the process is killed within the time."""
    interrupt_main = Mock()
    monkeypatch.setattr(_thread, "interrupt_main", interrupt_main)

    kill_after_delay(2)

    sleep(1)
    interrupt_main.assert_not_called()

    sleep(1.5)  # Give the kernel a chance.
    interrupt_main.assert_called_once()

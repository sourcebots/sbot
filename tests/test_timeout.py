"""Test the timeout function."""
from time import sleep

import os
import signal

from sbot.timeout import kill_after_delay
from unittest.mock import Mock


def test_kill_after_delay(monkeypatch) -> None:
    """Test that the process is killed within the time."""
    kill = Mock()
    pid = os.getpid()
    monkeypatch.setattr(os, "kill", kill)

    kill_after_delay(2)

    sleep(1)
    kill.assert_not_called()

    sleep(1.5)  # Give the kernel a chance.
    kill.assert_called_once_with(pid, signal.SIGTERM)

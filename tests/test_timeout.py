"""Test the timeout function."""
from time import sleep

import os
import signal
import subprocess
import sys

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


def test_kill_after_delay_e2e() -> None:
    child = subprocess.Popen([
        sys.executable,
        "-c",
        'from sbot.timeout import kill_after_delay; import time; kill_after_delay(2); time.sleep(10)'
    ])

    sleep(1)
    assert child.poll() is None

    sleep(2)
    assert abs(child.poll()) == signal.SIGTERM

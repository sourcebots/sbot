"""Test the timeout function."""
from time import sleep

import os
import signal
import subprocess
import sys
import pytest


from sbot.timeout import kill_after_delay


def test_kill_after_delay(monkeypatch) -> None:
    """Test that the process is killed within the time."""

    with pytest.raises(SystemExit):
        kill_after_delay(2)
        sleep(3)


def test_kill_after_delay_e2e() -> None:
    child = subprocess.Popen([
        sys.executable,
        "-c",
        'from sbot.timeout import kill_after_delay; import time; kill_after_delay(2); time.sleep(10)',
    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    sleep(1)
    assert child.poll() is None

    sleep(2)
    assert child.poll() == 0

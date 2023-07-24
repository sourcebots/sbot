"""Test the timeout function."""
from time import sleep, time

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
    start_time = time()
    child = subprocess.Popen([
        sys.executable,
        "-c",
        'from sbot.timeout import kill_after_delay; import time; kill_after_delay(2); time.sleep(10)',
    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    child.wait(timeout=5)

    assert time() - start_time == pytest.approx(2, rel=1)

    if sys.platform == "win32":
        # Windows terminates uncleanly
        assert child.returncode == signal.SIGTERM
    else:
        assert child.returncode == 0

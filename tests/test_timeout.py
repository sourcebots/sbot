"""Test the timeout function."""
from time import sleep, time

import os
import signal
import subprocess
import sys
import pytest
from unittest.mock import Mock

from sbot.timeout import kill_after_delay

@pytest.mark.skipif(sys.platform == "win32", reason="does not run on Windows")
def test_kill_after_delay() -> None:
    """Test that the process is killed within the time."""
    with pytest.raises(SystemExit):
        kill_after_delay(2)
        sleep(3)


@pytest.mark.skipif(sys.platform != "win32", reason="only runs on Windows")
def test_kill_after_delay_windows(monkeypatch) -> None:
    """Test that the process is killed within the time on windows."""
    kill = Mock()
    pid = os.getpid()
    monkeypatch.setattr(os, "kill", kill)

    kill_after_delay(2)
    sleep(1)

    kill.assert_not_called()

    sleep(1.5)
    kill.assert_called_once_with(pid, signal.SIGTERM)


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

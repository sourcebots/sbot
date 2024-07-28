"""Test the timeout function."""
from time import sleep, time

import os
from pathlib import Path
import signal
import subprocess
import sys
import pytest
from unittest.mock import Mock

from sbot.timeout import kill_after_delay

TEST_FILES = list((Path(__file__).parent / 'test_data/timeout_scripts').iterdir())

@pytest.mark.skipif(sys.platform == "win32", reason="does not run on Windows")
def test_kill_after_delay() -> None:
    """Test that the process is killed within the time."""
    with pytest.raises(SystemExit):
        kill_after_delay(2)
        sleep(3)

    # Clear the set alarm
    signal.alarm(0)


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


@pytest.mark.parametrize(
    "test_file",
    TEST_FILES,
    ids=[f.name for f in TEST_FILES]
)
def test_kill_after_delay_e2e(test_file: Path) -> None:
    start_time = time()
    child = subprocess.Popen([
        sys.executable,
        str(test_file),
    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    child.wait(timeout=6)
    run_time = time() - start_time

    assert run_time < 6

    if test_file.name != "early-exit.py":
        assert run_time > 2

    if sys.platform == "win32":
        # Windows terminates uncleanly
        assert child.returncode == signal.SIGTERM
    else:
        # Either the process was killed cleanly, or the fallback did
        assert child.returncode in [0, -signal.SIGALRM]

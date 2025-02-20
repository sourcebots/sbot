"""Test the timeout function."""
import os
import signal
import subprocess
import sys
from pathlib import Path
from time import sleep, time
from unittest.mock import Mock

import pytest

from sbot.internal.timeout import kill_after_delay

TEST_FILES = list((Path(__file__).parent / 'test_data/timeout_scripts').iterdir())
EXTRA_TEST_FILES_DIR = Path(__file__).parent / 'test_data/timeout_scripts_extra'


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
    ids=[f.stem for f in TEST_FILES]
)
def test_kill_after_delay_e2e(test_file: Path) -> None:
    start_time = time()
    child = subprocess.Popen([
        sys.executable,
        str(test_file),
    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    child.wait(timeout=8)
    run_time = time() - start_time

    assert 2 < run_time < 8

    if sys.platform == "win32":
        # Windows terminates uncleanly
        assert child.returncode == signal.SIGTERM
    elif run_time < 4:
        # If the process terminated quickly, it should be successful
        assert child.returncode == 0
    else:
        # If the process took too long, it was killed ungracefully
        assert child.returncode == -signal.SIGALRM

def test_early_exit() -> None:
    start_time = time()
    child = subprocess.Popen([
        sys.executable,
        str(EXTRA_TEST_FILES_DIR / "early-exit.py"),
    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    child.wait(timeout=6)

    run_time = time() - start_time

    assert run_time < 2

    assert child.returncode == 0

def test_exception() -> None:
    start_time = time()
    child = subprocess.Popen([
        sys.executable,
        str(EXTRA_TEST_FILES_DIR / "exception.py"),
    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    child.wait(timeout=6)

    run_time = time() - start_time

    assert run_time < 2

    assert child.returncode == 1

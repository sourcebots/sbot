"""Test the timeout function."""
import sys
from time import sleep

import pytest

from sbot.timeout import kill_after_delay


@pytest.mark.skipif(sys.platform == "win32", reason="does not run on windows")
def test_kill_after_delay() -> None:
    """Test that a SystemExit is raised within the time."""
    with pytest.raises(SystemExit):
        kill_after_delay(5)
        sleep(6)  # Kill within 6 seconds to give the kernel a chance.

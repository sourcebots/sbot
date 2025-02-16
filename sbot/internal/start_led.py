"""Start LED functionality for the KCH hat."""
from __future__ import annotations

import atexit

from sbot._utils import IN_SIMULATOR

from .._leds import RobotLEDs

try:
    import RPi.GPIO as GPIO  # isort: ignore
    HAS_HAT = True if not IN_SIMULATOR else False
except ImportError:
    HAS_HAT = False


# Start LED is initialised in the LED class
if HAS_HAT:
    _PWM: GPIO.PWM | None = None

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(RobotLEDs.START, GPIO.OUT, initial=GPIO.LOW)

    # Cleanup just the start LED to turn it off when the code exits
    # Mypy isn't aware of the version of atexit.register(func, *args)
    atexit.register(GPIO.cleanup, RobotLEDs.START)  # type: ignore[call-arg]


def flash_start_led() -> None:
    """Flash the start LED."""
    global _PWM

    if HAS_HAT:
        _PWM = GPIO.PWM(RobotLEDs.START, 1)
        _PWM.start(50)


def set_start_led(state: bool) -> None:
    """Set the state of the start LED."""
    global _PWM

    if HAS_HAT:
        # Clear the PWM if it is running
        if _PWM:
            _PWM.stop()
            _PWM = None

        GPIO.output(RobotLEDs.START, GPIO.HIGH if state else GPIO.LOW)

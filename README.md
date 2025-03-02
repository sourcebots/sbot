# sbot

[![Lint & build](https://github.com/sourcebots/sbot/actions/workflows/test_build.yml/badge.svg)](https://github.com/sourcebots/sbot/actions/workflows/test_build.yml)
[![PyPI version](https://badge.fury.io/py/sbot.svg)](https://badge.fury.io/py/sbot)
[![Documentation Status](https://readthedocs.org/projects/sbot/badge/?version=stable)](https://docs.sourcebots.co.uk)
[![MIT license](https://img.shields.io/badge/license-MIT-brightgreen.svg?style=flat)](https://opensource.org/licenses/MIT)
![Bees](https://img.shields.io/badge/bees-110%25-yellow.svg)

`sbot` - SourceBots Robot API

This is the API for Southampton Robotics Outreach robotics competitions.

## Installation

If you wish to install openCV from your package manager, you can install the base package with:

```bash
pip install sbot
```

To install the full package, including openCV, you can install with:

```bash
pip install sbot[vision]
```

## Usage

Importing the module will, by default, trigger board discovery and wait for the start button to be pressed.

```python
import sbot
```

Unlike previous versions, robot functionality is accessed directly from the `sbot` library instead of instantiating a class.

```python
from sbot import *

motors.set_power(0, 0.3)
motors.set_power(1, 0.3)

power.get_output_current(PowerOutputPosition.H0)
utils.sound_buzzer(880, 0.5)

servos.set_position(0, 45/90)

print(arduino.measure_ultrasound_distance(8, 9))

if comp.is_competition:
    markers = vision.detect_markers()
    leds.set_colour(0, Colour.MAGENTA)
```

### Startup behaviour

You can configure the startup behaviour of `sbot` with an `override.env` file in the same directory as your project.

Example `override.env` file:

```sh
ENABLE_DEBUG_LOGGING=1
SKIP_WAIT_START=1
NO_POWERBOARD=1
```

If `SKIP_WAIT_START` is set, you will have to manually trigger board discovery and wait for the start button:

```python
from sbot import utils

utils.load_boards()
utils.wait_start()
```

The currently supported override keys are:

Override | Description
--- | ---
ENABLE_DEBUG_LOGGING | Enable debug logging
ENABLE_TRACE_LOGGING | Enable trace level logging
SKIP_WAIT_START | Don't block for the start signal automatically
NO_POWERBOARD | Allow running without a power board
MANUAL_POWER_PORTS | Specify additional serial ports for power boards
MANUAL_MOTOR_PORTS | Specify additional serial ports for motor boards
MANUAL_SERVO_PORTS | Specify additional serial ports for servo boards
MANUAL_ARDUINO_PORTS | Specify additional serial ports for arduino boards
MANUAL_LED_PORTS | Specify additional serial ports for led boards, only used in the simulator
MANUAL_TIME_PORTS | Specify additional serial ports for the time interface, only used in the simulator
SORT_POWER_ORDER | Override the sort order of the power boards, unused
SORT_MOTOR_ORDER | Override the sort order of the motor boards
SORT_SERVO_ORDER | Override the sort order of the servo boards
SORT_ARDUINO_ORDER | Override the sort order of the arduino boards, unused
SORT_LED_ORDER | Override the sort order of the led boards, unused
SORT_TIME_ORDER | Override the sort order of the time interface, unused

You can also configure these settings as environment variables, by prepending the prefix `SBOT_`. For example, `ENABLE_DEBUG_LOGGING` can be set as `SBOT_ENABLE_DEBUG_LOGGING`. 
Some settings can only be configured as environment variables. These are:

Environment Variable | Description
--- | ---
OPENCV_CALIBRATIONS | Override the location to look for additional camera calibrations, defaults to the working directory
SBOT_METADATA_PATH | Override the location to look for metadata files, normally configured by the runner
SBOT_PYTEST | Set to `1` when running unit tests, to disable automatic discovery on import
SBOT_MQTT_URL | The URI to use for the MQTT broker, normally configured by the runner
run_uuid | The UUID to include in all MQTT messages, normally configured by the runner
WEBOTS_SIMULATOR | Set to `1` when running in the Webots simulator, used to detect the simulator environment
WEBOTS_ROBOT | List of socket URIs to connect to for the simulated boards, configured by the runner
WEBOTS_DEVICE_LOGGING | Set to the log level name to use for logging of the simulated boards, defaults to `WARNING`

## Developer Notes

There are a number of considerations that have been made in the design of this API.
Some of these may not be immediately obvious, so they are documented below.

- `tuple` is used to prevent the user from adding, removing or overwriting items in any parts of the API that would return a list.
- `__slots__` is used to prevent the user from adding, removing or overwriting attributes in any parts of the API.
- `sbot.serial_wrapper.SerialWrapper` handles automatic reconnection to the serial port if the connection is lost and impleents 3 retries on any serial operation before raising a `BoardDisconnectionError`.
- The old API is still available under `sbot.historic`, though this might change.

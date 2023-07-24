# sbot

[![Lint & build](https://github.com/sourcebots/sbot/actions/workflows/test_build.yml/badge.svg)](https://github.com/sourcebots/sbot/actions/workflows/test_build.yml)
[![PyPI version](https://badge.fury.io/py/sbot.svg)](https://badge.fury.io/py/sbot)
[![Documentation Status](https://readthedocs.org/projects/pip/badge/?version=stable)](http://pip.pypa.io/en/stable/?badge=stable)
[![MIT license](https://img.shields.io/badge/license-MIT-brightgreen.svg?style=flat)](https://opensource.org/licenses/MIT)
![Bees](https://img.shields.io/badge/bees-110%25-yellow.svg)

`sbot` - SourceBots Robot API

This is the API for SourceBots, library for writing Robotics APIs.
It will first be deployed at Smallpeice 2023.

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

The main entry point for the API is the `Robot` class.
Intantiating this class will automatically detect and connect to any SR v4 boards connected to the device.
By default, the `Robot` class will wait for the start button on the power board to be pressed before continuing.

```python

from sbot import Robot

r = Robot()

```

To disable the waiting for the start button, you can pass `wait_for_start=False` to the constructor.
The `wait_for_start` method needs to be called before the metadata is available.

```python

from sbot import Robot

r = Robot(wait_for_start=False)

# Setup in here

r.wait_start()

```

## Developer Notes

There are a number of considerations that have been made in the design of this API.
Some of these may not be immediately obvious, so they are documented below.

- The API is designed to raise exceptions for incorrect actions, such as trying to modify the output dictionary or assign a value directly to the motor object.
- `MappingProxyType` is used to prevent the user from adding, removing or overwriting keys in any parts of the API that return a dictionary.
- `tuple` is used to prevent the user from adding, removing or overwriting items in any parts of the API that would return a list.
- `__slots__` is used to prevent the user from adding, removing or overwriting attributes in any parts of the API.
- `sbot.serial_wrapper.SerialWrapper` handles automatic reconnection to the serial port if the connection is lost and impleents 3 retries on any serial operation before raising a `BoardDisconnectionError`.

# sbot

[![CircleCI](https://circleci.com/gh/sourcebots/sbot.svg?style=svg)](https://circleci.com/gh/sourcebots/sbot)
[![PyPI version](https://badge.fury.io/py/sbot.svg)](https://badge.fury.io/py/sbot)
[![Documentation Status](https://readthedocs.org/projects/pip/badge/?version=stable)](http://pip.pypa.io/en/stable/?badge=stable)
[![MIT license](https://img.shields.io/badge/license-MIT-brightgreen.svg?style=flat)](https://opensource.org/licenses/MIT)
![Bees](https://img.shields.io/badge/bees-110%25-yellow.svg)

`sbot` - SourceBots Robot API - Powered by j5

This is the API for SourceBots, based on the [j5](https://github.com/j5api/j5)
library for writing Robotics APIs. It will first be deployed at Smallpeice 2019.

Much like it's predecessor, [robot-api](https://github.com/sourcebots/robot-api), `sbot` supports
multiple backends, although should be more reliable as there is no `UNIX-AF` socket layer.

## Installation

Install: `pip install sbot`

Install with vision support: `pip install sbot[vision]`

## Usage

```python

from sbot import Robot

r = Robot()

```

Or alternatively:

```python

from sbot import Robot

r = Robot(wait_start=False)

# Setup in here

r.wait_start()

```

## Adding camera calibrations

You will need to print off a [chAruco marker grid](https://docs.opencv.org/4.5.3/charuco_board.png).

`opencv_interactive-calibration -t=charuco -sz=GRID_SIZE`

Replace GRID_SIZE with the length of one of the larger squares (in mm) from the printed marker grid.

Use `-ci=1` for specifying camera index if multiple cameras are connected.

Point the camera at the marker grid. Until DF is at or below 30 then press S to save.
This will output a `cameraParameters.xml` file. Place this file in `sr/robot3/vision/calibrations` named by the camera model.

You will need to add a detection strategy for the camera in to `sr/robot3/vision/backend.py`.

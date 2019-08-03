# sbot

[![CircleCI](https://circleci.com/gh/sourcebots/sbot.svg?style=svg)](https://circleci.com/gh/sourcebots/sbot)
[![PyPI version](https://badge.fury.io/py/sbot.svg)](https://badge.fury.io/py/sbot)
[![Documentation Status](https://readthedocs.org/projects/pip/badge/?version=stable)](http://pip.pypa.io/en/stable/?badge=stable)

`sbot` - SourceBots Robot API - Powered by j5

This is the API for SourceBots, based on the [j5](https://github.com/j5api/j5)
library for writing Robotics APIs. It will first be deployed at Smallpeice 2019.

Much like it's predecessor, [robot-api](https://github.com/sourcebots/robot-api), `sbot` supports
multiple backends, although should be more reliable as there is no `UNIX-AF` socket layer.

## Installation

Once published:

Install: `pip install sbot`
Install with vision support: `pip install sbot j5[zoloto-vision]`

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

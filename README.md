# sbot

`sbot` - SourceBots Robot API - Powered by j5

This is an experimental API for SourceBots, based on the [j5](https://github.com/j5api/j5)
library for writing Robotics APIs. If successful, it could potentially be deployed at
SourceBots / Smallpeice 2019.

Much like it's predecessor, [robot-api](https://github.com/sourcebots/robot-api), `sbot` supports
multiple backends, although should be more reliable as there is no `UNIX-AF` socket layer.

## Installation

Once published:

Install: `pip install sbot`

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
# sbot

[![Lint & build](https://github.com/sourcebots/sbot/actions/workflows/check.yml/badge.svg)](https://github.com/sourcebots/sbot/actions/workflows/check.yml)
[![PyPI version](https://badge.fury.io/py/sbot.svg)](https://badge.fury.io/py/sbot)
[![Documentation Status](https://readthedocs.org/projects/pip/badge/?version=stable)](http://pip.pypa.io/en/stable/?badge=stable)
[![MIT license](https://img.shields.io/badge/license-MIT-brightgreen.svg?style=flat)](https://opensource.org/licenses/MIT)
![Bees](https://img.shields.io/badge/bees-110%25-yellow.svg)

`sbot` - SourceBots Robot API - Powered by j5

This is the API for SourceBots, library for writing Robotics APIs.
It will first be deployed at Smallpeice 2023.

## Installation

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

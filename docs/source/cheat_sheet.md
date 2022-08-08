---
layout: page
title: API Quick Reference
---

# SR API Quick Reference

This page contains a quick guide to the `sr.robot3` API.

For more information, make sure you check the rest of the documentation.

## Initialising your robot

### Standard Initialisation

~~~~~ python
from sbot import *

R = Robot()
~~~~~

### Initialisation without waiting for the start button

~~~~~ python
R = Robot(auto_start=True)

# Code here runs before the start button is pressed

R.wait_start()
~~~~~

### Initialisation with extra logging

You can also tell the robot to print extra logging information, although this is quite noisy.

~~~~~ python
R = Robot(verbose=True)
~~~~~

## Selecting which board to control

If you only have one board of a given type plugged into your robot, then you can use its singular name:

~~~~~ python
R.power_board.something
R.motor_board.something
R.servo_board.something
R.ruggeduino.something
~~~~~

If you have multiple boards of a given type plugged into your robot, you must index them by serial number:

~~~~~ python
R.motor_boards["srABC1"].something
R.servo_boards["srXYZ2"].something
R.ruggeduinos["1234567890"].something
~~~~~

## Power Board

The outputs on the power board will turn on when you initialise your robot.

### Turn on and off the power outputs

~~~~~ python
# Turn all of the outputs on
R.power_board.outputs.power_on()

# Turn all of the outputs off
R.power_board.outputs.power_off()

# Turn a single output on
R.power_board.outputs[OUT_H0].is_enabled = True

# Turn a single output off
R.power_board.outputs[OUT_H0].is_enabled = False
~~~~~

### Reading voltage and current

~~~~~ python
# Read the current of an individual output
current = R.power_board.outputs[OUT_H0].current

# Read the current and voltage from the LiPo battery
voltage = R.power_board.battery_sensor.voltage
current = R.power_board.battery_sensor.current
~~~~~

### Buzzer

The power board has an on-board piezoelectric buzzer.

~~~~~ python
# Play a standard note C6 -> C8 included for 0.5s
R.power_board.piezo.buzz(0.5, Note.C6)

# Play a tone at 1047Hz for 1 second
R.power_board.piezo.buzz(1, 1047)
~~~~~

## Motors

### Powering Motors

You can set the power of each motor on the board between -1 and 1.

If you change the power of your motor too rapidly, the overcurrent protection may be triggered.

~~~~~ python
R.motor_board.motors[0].power = 1
R.motor_board.motors[1].power = -1
~~~~~

Setting a motor to `COAST` is equivalent to power level `0`.

~~~~~ python
# This is the same operation
R.motor_board.motors[0].power = COAST
R.motor_board.motors[0].power = 0
~~~~~

### Braking Motors

You can also brake a motor, which will quickly slow the motor.

~~~~~ python
R.motor_board.motors[0].power = BRAKE
R.motor_board.motors[1].power = -1
~~~~~

## Servos

You can set the position of each servo output on the board between -1 and 1.

~~~~~ python
R.servo_board.servos[0].position = -1
R.servo_board.servos[1].position = 1
~~~~~

You can also set the position to `0`, which is the approximate centre.

This is different to setting the position to `None`, which will unpower the servo.

~~~~~ python
# This servo is now unpowered, and will move more freely.
R.servo_board.servos[11].position = None
~~~~~

## Camera

### Taking a photo

It can sometimes be useful to save a photo of what markers the robot can see:

~~~~~ python
R.camera.save("my-photo.png")  # Save my-photo.png to the USB drive
~~~~~

### Looking for markers

You can take a photo with the camera and search for markers:

~~~~~ python
markers = R.camera.see()
~~~~~

There are various bits of information available about visible markers:

~~~~~ python
for marker in markers:

    marker.id  # The ID of the marker
    marker.size  # Physical size of the marker in mm.

    marker.distance  # Distance away from the camera in mm

    # Cartesian coords of the marker
    marker.cartesian.x
    marker.cartesian.y
    marker.cartesian.z

    # Spherical coords of the marker
    marker.spherical.rot_x
    marker.spherical.rot_y
    marker.spherical.dist

    # Orientation of the marker
    marker.orientation.rot_x
    marker.orientation.rot_y
    marker.orientation.rot_z
    marker.orientation.rotation_matrix
~~~~~

## Ruggeduino

### Setting the mode of a pin

~~~~~ python
R.ruggeduino.pins[4].mode = OUTPUT
R.ruggeduino.pins[4].mode = INPUT
R.ruggeduino.pins[4].mode = INPUT_PULLUP
~~~~~

### Digital Write

You can set the output for a pin of the Ruggeduino:

~~~~~ python
R.ruggeduino.pins[4].mode = OUTPUT

R.ruggeduino.pins[2].digital_write(True)
R.ruggeduino.pins[2].digital_write(False)
~~~~~

### Digital Read

You can read a digital value from the pins of the Ruggeduino:

~~~~~ python
R.ruggeduino.pins[3].mode = INPUT

value = R.ruggeduino.pins[3].digital_read()
~~~~~

### Analogue Read

You can read an analogue value from the analogue pins of the Ruggeduino:

~~~~~ python
value = R.ruggeduino.pins[A0].analogue_read()
~~~~~

## Metadata

The API also makes some information about where your code is running

### Starting Zone for a match

~~~~~ python
zone = R.zone  # -> 0, 1, 2, or 3
~~~~~

### Arena Information

~~~~~ python
arena = R.arena # -> 'A'
~~~~~

### Robot Mode

This is set to `COMP` when your robot is in a match.

~~~~~ python
robot_mode = R.mode # -> DEV or COMP
~~~~~

### USB Key Path

This is the path to where your USB key is mounted.

You can use this to save files and information to the drive.

~~~~~ python
usb_key_path = R.usbkey # -> pathlib.Path
~~~~~

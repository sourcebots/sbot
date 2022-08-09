# SourceBots API Quick Reference

This page contains a quick guide to the `sbot` API.

For more information, make sure you check the rest of the documentation.

## Initialising your robot

### Standard Initialisation

~~~~~ python
from sbot import *

r = Robot()
~~~~~

### Initialisation without waiting for the start button

~~~~~ python
r = Robot(wait_start=False)

# Code here runs before the start button is pressed

r.wait_start()
~~~~~

### Initialisation with extra logging

You can also tell the robot to print extra logging information, although this is quite noisy.

~~~~~ python
r = Robot(debug=True)
~~~~~

## Selecting which board to control

If you only have one board of a given type plugged into your robot, then you can use its singular name:

~~~~~ python
r.power_board.something
r.motor_board.something
r.servo_board.something
r.arudino.something
~~~~~

If you have multiple boards of a given type plugged into your robot, you must index them by serial number:

~~~~~ python
r.motor_boards["srABC1"].something
r.servo_boards["SRO-ABC-XYZ"].something
~~~~~

## Power Board

The outputs on the power board will turn on when you initialise your robot.

### Turn on and off the power outputs

~~~~~ python
# Turn all of the outputs on
r.power_board.outputs.power_on()

# Turn all of the outputs off
r.power_board.outputs.power_off()

# Turn a single output on
r.power_board.outputs[H0].is_enabled = True

# Turn a single output off
r.power_board.outputs[H0].is_enabled = False
~~~~~

### Reading voltage and current

~~~~~ python
# Read the current of an individual output
current = r.power_board.outputs[H0].current

# Read the current and voltage from the LiPo battery
voltage = r.power_board.battery_sensor.voltage
current = r.power_board.battery_sensor.current
~~~~~

### Buzzer

The power board has an on-board piezoelectric buzzer.

~~~~~ python
# Play a standard note C6 -> C8 included for 0.5s
r.power_board.piezo.buzz(0.5, Note.C6)

# Play a tone at 1047Hz for 1 second
r.power_board.piezo.buzz(1, 1047)
~~~~~

## Motors

### Powering Motors

You can set the power of each motor on the board between -1 and 1.

If you change the power of your motor too rapidly, the overcurrent protection may be triggered.

~~~~~ python
r.motor_board.motors[0].power = 1
r.motor_board.motors[1].power = -1
~~~~~

Setting a motor to `COAST` is equivalent to power level `0`.

~~~~~ python
# This is the same operation
r.motor_board.motors[0].power = COAST
r.motor_board.motors[0].power = 0
~~~~~

### Braking Motors

You can also brake a motor, which will quickly slow the motor.

~~~~~ python
r.motor_board.motors[0].power = BRAKE
r.motor_board.motors[1].power = -1
~~~~~

## Servos

You can set the position of each servo output on the board between -1 and 1.

~~~~~ python
r.servo_board.servos[0].position = -1
r.servo_board.servos[1].position = 1
~~~~~

You can also set the position to `0`, which is the approximate centre.

This is different to setting the position to `None`, which will unpower the servo.

~~~~~ python
# This servo is now unpowered, and will move more freely.
r.servo_board.servos[11].position = None
~~~~~

## Camera

### Taking a photo

It can sometimes be useful to save a photo of what markers the robot can see:

~~~~~ python
r.camera.save("my-photo.png")  # Save my-photo.png to the USB drive
~~~~~

### Looking for markers

You can take a photo with the camera and search for markers:

~~~~~ python
markers = r.camera.see()
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

## Arduino

### Setting the mode of a pin

~~~~~ python
r.arduino.pins[4].mode = OUTPUT
r.arduino.pins[4].mode = INPUT
r.arduino.pins[4].mode = INPUT_PULLUP
~~~~~

### Digital Write

You can set the output for a pin of the Arduino:

~~~~~ python
r.arduino.pins[4].mode = OUTPUT

r.arduino.pins[2].digital_write(True)
r.arduino.pins[2].digital_write(False)
~~~~~

### Digital Read

You can read a digital value from the pins of the Arduino:

~~~~~ python
r.arduino.pins[3].mode = INPUT

value = r.arduino.pins[3].digital_read()
~~~~~

### Analogue Read

You can read an analogue value from the analogue pins of the Arduino:

~~~~~ python
value = r.arduino.pins[A0].analogue_read()
~~~~~

## Metadata

The API also makes some information about where your code is running

### Starting Zone for a match

~~~~~ python
zone = r.zone  # -> 0, 1, 2, or 3
~~~~~

### Competition mode

This is `True` when your robot is in a match.

~~~~~ python
robot_mode = r.is_competition # -> True or False
~~~~~

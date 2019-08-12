Using Your Kit
========================

.. Hint:: In this tutorial, we will be using our API (Application 
   Programming Interface), which is the functions you need to use to make the robot
   do stuff, so make sure to have a look at it first!

Setup
--------
Before you start this tutorial, make sure you have `connected your 
kit together`_.

.. _connected your kit together: connecting-your-kit

There are two lines of code you must have at the very top of your code whenever 
you want to do something with the robot, those lines are:

.. code:: python

    from sbot import *

    r = Robot()

These two lines simply copy in all of our helper functions, and sets up your 
robot.

Any code below the line with ``r = Robot()`` won't be run until you hit the
black 'Start' button on the power board.

Forwards and Backwards
----------------------

Start by checking that you can drive your motors forwards and backwards.
Doing this is actually very easy; the only thing you need to realise is that a
positive number drives the motor in one direction and a negative number drives it in the other direction.

.. Warning:: Make sure your robots can turn without danger.
   If your motors aren't attached to a chassis, make sure they don't have wheels
   and are sitting in a position which makes it safe for them to turn.

Please remember that the actual movement of the robot depends which way around
the motor is mounted on the robot! It's very likely you might need to set one
motor to go in reverse in order for your robot to go forwards.

Here's the code:

.. code:: python

    from sbot import *
    from time import sleep
    r = Robot()
    while True:
        # Set motor 0 to 20% power.
        r.motor_board.motors[0].power = 0.2
        # Set motor 1 to 20% power
        r.motor_board.motors[1].power = 0.2

        sleep(1)

        r.motor_board.motors[0].power = 0
        r.motor_board.motors[1].power = 0

        sleep(1)

You’re hopefully familiar with the first few lines; in fact, the only lines you 
may not be familiar with are the ``r.motor_board.motors[0]``... lines. For a
comprehensive reference to the 'motor' object, see `the motor page 
</en/latest/api/motor-board.html>`_. 

But, to summarise:

.. code:: python

    r.motor_board.motors[0].power = x

will set the power of the
motor connected to output 0 (the ``motors[0]`` part) on the motor board to 
``x``, where ``x`` is a value between ``-1`` and ``1``, inclusive.

Now see if you can turn on the spot, then try driving in various shapes.

Write some code that would make your robot drive in:
- a square
- a wavy line

Changing the speed
------------------

When you move your robot, it's likely you'll want your robot to go from stand-
still to moving at a high speed. The most obvious way of doing this is to just immediately
set the power of the motors from ``0`` to ``1``.

There are 2 problems with doing this:

1. Setting the power from ``0`` to ``1`` very quickly draws a very large current
   from the motor, so much so that it might trip the over-current protection on our power board.
2. Quickly changing the speed can cause the wheels to slip, meaning your robot
   won't necessarily go the distance or direction you expect it to.

There's a simple solution to this, whenever you speed up or slow down, you 
should write some code which smoothly changes the motor speed from 0 to the
target speed.

Firstly, how do you smoothly change the robot speed?

It's pretty simple once you understand it:

.. code:: python

    from sr.robot import *
    import time

    R = Robot()

    for power in range(0, 101):
          r.motor_board.motors[0].power = power / 100
          time.sleep(0.01)


This code should smoothly speed up your motor from 0 to 1 in 1 second.

The python ``range`` function takes in 2 parameters, ``from`` and ``to``. It then
simply returns a list of numbers between those two values. It *doesn't* give
you the last number. (i.e. ``range(0,3)`` will give you a list containing 0, 1, 
and 2) So if you want the last number you'll need to go one further.

The ``time.sleep`` is there otherwise the code will immediately go to full
power.

Now try and write some code that:
- Smoothly starts and stops your robot.

Servos
------

Servos are a motor which knows what position it's at. You can tell it an angle
and it'll handle turning to that value! 

.. Warning:: Be warned, most servos can't turn a full 360 degrees!
Always check how far it can move before you design a cool robot arm!

Servos can be set to turn to a specific position. Sadly you can't just tell it
an angle to turn to in degrees, you can only tell it to go between ``-1`` and 
``1``. You'll need to measure the angle yourself and work this out if you need
it!

If you plug a servo in channel '0' of the servo board, this code will turn it 
back and forth from minimum to maximum forever:

.. code:: python

    from sbot import *
    from time import sleep

    r = Robot()

    r.servo_board.servos[0].position = 1

    while True:
        r.servo_board.servos[0].position = -r.servo_board.servos[0].position
        sleep(1)

This works because you can get the last position you told the servo to go to 
with ``blah = r.servo_board.servos[0].position``

Now connect 2 servos to your robot. See if you can spell out
"Hello" in `Semaphore <https://en.wikipedia.org/wiki/Flag_semaphore>`__.
You will have to think about which way to orient your servos so they
can reach all of the positions they need to. You can add paper flags
to your servos if you want to.

Ultrasound
----------

An Ultrasound Sensor can be used to measure distances.

The sensor sends a pulse of sound at the object and then measures the time taken
for the reflection to be heard.

The ultrasound sensors aren't lasers, they have a cone-shaped range, and give 
you the distance of the nearest large thing. Also ultrasound sensors have both a
minimum and a maximum range! Make sure you know what the minimum range is for
your sensor by experimenting with it.

.. code:: python

    from sbot import *
    from time import sleep

    r = Robot()

    while True:
        distance = r.arduino.ultrasound_sensors[4, 5].distance()
        print("Object is {}m away.".format(distance))
        sleep(1)

This code will print the distance in metres to the log file every second.

Try write some code that spins your motors forward, but stop when a object closer
than 20cm is detected by the ultrasound sensor.

Buzzer
------

The power board on your kit has a `piezoelectric
buzzer <https://www.engineersgarage.com/insight/how-piezo-buzzer-works>`__
onboard. We can use this to play tunes and make sounds, which can be useful 
when trying to figure out what your code is doing live.

.. code:: python

    from sbot import *
    from time import sleep

    r = Robot()

    # Play a tone of 1000Hz for 1 second.
    r.power_board.piezo.buzz(1, 1000)

    # Play A7 for 1 second.
    r.power_board.piezo.buzz(1, Note.A7)

.. Hint:: Notes from ``C6`` to ``C8`` are available. You can play other tones by
 looking up the frequency 
 `here <https://en.wikipedia.org/wiki/Scientific_pitch_notation#Table_of_note_frequencies>`__.

Building a Theremin
-------------------

A Theremin is a unusual musical instrument that is controlled by the distance
your hand is from its antennae.

.. figure:: /_static/tutorials/using-your-kit/theremin.jpg
   :alt: Theremin
   :scale: 75%

   A Moog Etherwave, assembled from a theremin kit: the loop antenna on the left
   controls the volume while the upright antenna controls the pitch.

Can you use your ultrasound sensor and buzzer to build a basic Theremin?

Here's some code to help you get started:

.. code:: python

    from sbot import *
    from time import sleep

    r = Robot()

    while True:
        distance = ...

        pitch_length = ...

        # Remember, humans can hear between about 2000Hz and 20,000Hz
        pitch_to_play = ...

        r.power_board.piezo.buzz(pitch_length, pitch_to_play)
        sleep(pitch_length)

Inputs and Outputs
------------------

The Arduino has some pins on it that can allow your robot to sense it's
environment.

We will investigate how these work in more detail in the electronics labs, but
we can run some code anyway.

.. code:: python

    from sbot import *
    from time import sleep

    # Turn on the pins
    for pin in r.arduino.pins:
        pin.mode = GPIOPinMode.DIGITAL_OUTPUT
        pin.digital_state = True

    # Flash all of the pins.
    while True:
        pin.digital_state = not pin.digital_state
        sleep(0.5)

Using Your Kit
========================

.. Hint:: Throughout this tutorial, we will be using the API, so make sure to have a look first!

Setup
--------
Before you start this tutorial, make sure you are familiar with Connecting Your Kit and Setup.

Basic Movement
----------------

Start by checking that you can drive your robot in a straight line.
Here is some demo code:

.. code:: python

    from sbot import *
    from time import sleep

    r = Robot()

    r.motor_board.motors[0].power = 0.2
    r.motor_board.motors[1].power = 0.2

    sleep(1)

    r.motor_board.motors[0].power = 0
    r.motor_board.motors[1].power = 0

Now see if you can turn on the spot, then try driving in various shapes.

Can you drive in:
- a square?
- an equilateral triangle?
- a circle?
- a wavy line?

Servos
------

Servos can be set to turn to a specific position. On your robot,
this will be somewhere between ``-1`` and ``1``. This code will turn a servo
connected to the channel '0' back and forth forever:

.. code:: python

    from sbot import *
    from time import sleep

    r = Robot()

    r.servo_board.servos[0].position = 1

    while True:
        r.servo_board.servos[0].position *= 1
        sleep(1)

Now connect 2 servos to your robot. See if you can spell out
"Hello" in `Semaphore <https://en.wikipedia.org/wiki/Flag_semaphore>`__.
You will have to think about which way to orient your servos so they
can reach all of the positions they need to. You can add paper flags
to your servos if you want to.

Ultrasound
----------

An Ultrasound Sensor can be used to measure distances of objects.

The sensor sends a pulse of sound at the object and then measures the time taken for the reflect

.. code:: python

    from sbot import *
    from time import sleep

    r = Robot()

    while True:
        distance = r.arduino.ultrasound_sensors[4, 5].distance()
        print("Object is " + distance + "m away.")
        sleep(1)

This code will print the distances to the log.

Try to spin your motors forward, but stop when a object is nearby.

Buzzer
------

The power board on your kit has a `piezo
buzzer <https://www.engineersgarage.com/insight/how-piezo-buzzer-works>`__
onboard. We can use this to play tunes and make sounds, which can be useful 
when debugging your code.

.. code:: python

    from sbot import *
    from time import sleep

    r = Robot()

    # Play a tone of 1000Hz for 1 second.
    r.power_board.piezo.buzz(1, 1000)

    # Play A7 for 1 second.
    r.power_board.piezo.buzz(1, Note.A7)

.. Hint:: Notes from ``C6`` to ``C8`` are available. You can play other tones by looking up the frequency `here <https://en.wikipedia.org/wiki/Scientific_pitch_notation#Table_of_note_frequencies>`__.


Building a Theremin
-------------------

A Theremin is a unusual musical instrument that is controlled by the distance your hand is from its antennae.

.. figure:: /_static/tutorials/using-your-kit/theremin.jpg
   :alt: Theremin
   :scale: 75%

   A Moog Etherwave, assembled from a theremin kit: the loop antenna on the left controls the volume while the upright antenna controls the pitch.

Can you use your ultrasound sensor and buzzer to build a basic Theremin?

Here's some code to help you get started:

.. code:: python

    from sbot import *
    from time import sleep

    r = Robot()

    while True:
        distance = ???

        # Remember, humans can hear between about 2000Hz and 20,000Hz
        pitch_to_play = ???

        pitch_length = ???

        r.power_board.piezo.buzz(pitch_length, pitch_to_play)
        sleep(pitch_length)

Inputs and Outputs
------------------

The Arduino has some pins on it that can allow your robot to sense it's environment.

We will investigate how these work in more detail in the electronics labs, but we can run some code anyway.

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

Using Your Kit
========================

..Hint:: Throughout this tutorial, we will be using the API at
:ref: 'api/index'

Setup
--------
Before you start this tutorial, make sure you are familiar with
how to 'connect your kit :ref: connecting_your_kit' and
have read through ':ref: Setup' and ':ref: Running_your_code'

Basic Movement
----------------

Start by checking that you can drive your robot in a straight line.
Here is some demo code:

.. code:: python

    from sbot import Robot
    from time import sleep

    r = Robot()

    my_motor_board = r.motor_board

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

.. Hint:: Remember to refer back to ':ref: api/motor_board'


Servos
------------

Servos can be set to turn to a specific position. On your robots,
this will be somewhere between -1 and 1. This code will turn a servo
connected to the channel '0' back and forth forever:

.. code:: python

    from sbot import Robot
    from time import sleep

    r = Robot()

    my_servo_board = r.servo_board
    r.servo_board.servos[0].position = 1

    while(True):
        r.servo_board.servos[0].position *= 1
        sleep(1)

Now connect 2 servos to your robot. See if you can spell out
"Hello" in 'Semaphore <https://en.wikipedia.org/wiki/Flag_semaphore>'.
You will have to think about which way to orient your servos so they
can reach all of the positions they need to. You can add paper flags
to your servos if you want to.

.. Hint:: Don't forget about the API ':ref: api/servo_board' if you need it.


## Ultrasound
Show some simple code + give activity

## Buzzer
Play happy birthday

## Theremin
Maybe combine previous two

## Metal switch detector
how do use arduino

## Maybe some advanced stuff linking together
 - Stop 10 cm from wall?
 - Car Reversing (beeps + stop)

## Know which zone
Mention dev mode always = 0 + how to know if in dev mode
When in arena zone will change can be used for different straegies get it by this
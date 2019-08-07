API Documentation
=================

.. toctree::
   :titlesonly:
   :caption: Quick Links:
   
   arduino
   motor-board
   power-board
   servo-board

   game-state

Programming your robot is done in `Python <https://www.python.org/>`__,
specifically version 3.7.4. You can learn more about Python from their
`docs <https://docs.python.org/3/>`__, and our whirlwind tour.

Setup
-----

The following two lines are required to complete initialisation of the
kit:

.. code:: python

   from sbot import Robot

   r = Robot()

Once this has been done, this ``Robot`` object can be used to control
the robot’s functions.

The remainder of the tutorials pages will assume your ``Robot`` object
is defined as ``r``.

Running your code
-----------------

Your code needs to be put on a USB drive in a file called ``main.py``.
On insertion into the robot, this file will be executed. The file is
directly executed off your USB drive, with your drive as the working
directory.

To stop your code running, you can just remove the USB drive. This will
also stop the motors and any other peripherals connected to the kit.

You can then reinsert the USB drive into the robot and it will run your
``main.py`` again (from the start). This allows you to make changes and
test them quickly.

.. Hint:: If this file is missing or incorrectly named, your
  robot won’t do anything. No log file will be created.

Start Button
------------

After the robot has finished starting up, it will wait for the *Start
Button* on the power board to be pressed before continuing with your
code, so that you can control when it starts moving. There is a green
LED next to the start button which flashes when the robot is finished
setting up and the start button can be pressed.

Running Code before pressing the start button
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you want to do things before the start button press, such as setting
up servos or motors, you can pass ``wait_start`` to the ``Robot`` constructor. You will
then need to wait for the start button 
`manually <kit/power-board/#start-button>`__.

.. code:: python

   r = Robot(wait_start=False)

   # Do your setup here

   r.wait_start()

Logs
----

A log file is saved on the USB drive so you can see what your robot did,
what it didn’t do, and any errors it raised. The file is saved to
``log.txt`` in the top-level directory of the USB drive.

.. Warning:: The previous log file is deleted at the start of
   each run, so copy it elsewhere if you need to keep hold of it!

Serial number
-------------

All kit boards have a serial number, unique to that specific board,
which can be read using the ``serial`` property:

.. code:: python

   r.power_board.serial
   >>> 'SRO-AA2-7XS'
   r.servo_board.serial
   >>> 'SRO-AA4-LG2'
   r.motor_board.serial
   >>> 'SRO-AAO-RV2'

Included Libraries
------------------

Python already comes with plenty of `built-in
libraries <https://docs.python.org/3.7/py-modindex.html>`__
to use. We install some extra ones which may be of use:

-  `numpy <https://pypi.python.org/pypi/numpy>`__
-  `scipy <https://pypi.python.org/pypi/scipy>`__

Motor Board API
===============

The kit can control multiple motors simultaneously. One Motor Board can
control up to two motors.

Accessing Motor Boards
----------------------

The motor board can be accessed using the ``motor_board`` property of
the ``Robot`` object.

.. code:: python

   motor_board = r.motor_board

This board object has an array containing the motors connected to it,
which can be accessed as ``motor[0]`` and ``motor[1]``. The Motor Board is labelled so you know which
motor is which.

.. code:: python

   r.motor_board.motor[0]
   r.motor_board.motor[1]

Powering motors
---------------

Motor power is controlled using `pulse-width modulation
(PWM) <https://en.wikipedia.org/wiki/Pulse-width_modulation>`__. You set
the power with a fractional value between ``-1`` and ``1`` inclusive,
where ``1`` is maximum speed in one direction, ``-1`` is maximum speed
in the other direction and ``0`` causes the motor to brake.

.. code:: python

   r.motor_board.motor[0].power  = 1
   r.motor_board.motor[1].power = -1

These values can also be read back:

.. code:: python

   r.motor_board.motor[0].power
   >>> 1

   r.motor_board.motor[1].power
   >>> -1

.. Warning:: Setting a value outside of the range ``-1`` to
   ``1`` will raise an exception and your code will crash.

Special values
~~~~~~~~~~~~~~

In addition to the numeric values, there are two special constants that
can be used: ``BRAKE`` and ``COAST``. In order to use these, they must
be imported from the ``robot`` module like so:

.. code:: python

   from sbot import BRAKE, COAST

``BRAKE``
^^^^^^^^^

``BRAKE`` will stop the motors from turning, and thus stop your robot as
quick as possible.

.. Hint:: ``BRAKE`` does the same as setting the power to ``0``.

.. code:: python

   from sbot import BRAKE

   r.motor_board.motor[0].power = BRAKE

``COAST``
^^^^^^^^^

``COAST`` will stop applying power to the motors. This will mean they
continue moving under the momentum they had before.

.. code:: python

   from sbot import COAST

   r.motor_board.motor[1].power = COAST

.. Warning:: Sudden large changes in the motor speed setting
   (e.g. ``-1`` to ``0``, ``1`` to ``-1`` etc.) will likely trigger the
   over-current protection and your robot will shut down with a distinct beeping
   noise.

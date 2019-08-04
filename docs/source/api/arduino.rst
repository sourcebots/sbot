Arduino API
===========

The `Arduino <https://store.arduino.cc/arduino-uno-rev3>`__
provides a total of 18 pins for either digital input or output (labelled
2 to 13 and A0 to A5), including 6 for analogue input (labelled A0 to
A5).

Accessing the Arduino
---------------------

The Arduino can be accessed using the ``arduino`` property of
the ``Robot`` object.

.. code:: python

   my_arduino = r.arduino

You can use the GPIO *(General Purpose Input/Output)* pins for anything,
from microswitches to LEDs. GPIO is only available on pins 2 to 12, and A0 to A5
because pins 0 and 1 are reserved for communication with the rest of our
kit.

Pin mode
--------

GPIO pins have four different modes. A pin can only have one mode at a
time, and some pins aren’t compatible with certain modes. These pin
modes are represented by an
`enum <https://docs.python.org/3/library/enum.html>`__ which needs to be
imported before they can be used.

.. code:: python

   from sbot import GPIOPinMode

.. Hint:: The input modes closely resemble those of an
   Arduino. More information on them can be found in `their
   docs <https://www.arduino.cc/en/Tutorial/DigitalPins>`__.


``GPIOPinMode.DIGITAL_INPUT``
~~~~~~~~~~~~~~~~~

In this mode, the digital state of the pin (whether it is high or low)
can be read.

.. code:: python
   
   pin_value = r.arduinos.pins[4].digital_state


``GPIOPinMode.DIGITAL_INPUT_PULLUP``
~~~~~~~~~~~~~~~~~~~~~~~~

Same as ``GPIOPinMode.DIGITAL_INPUT``, but with an internal `pull-up
resistor <https://learn.sparkfun.com/tutorials/pull-up-resistors>`__
enabled.

.. code:: python
   
   pin_value = r.arduinos.pins[4].digital_state

``GPIOPinMode.DIGITAL_OUTPUT``
~~~~~~~~~~~~~~~~~~~~~~~

In this mode, we can set binary values of ``0V`` or ``5V`` to the pin.

.. code:: python
   
   r.arduinos.pins[4].digital_state = True
   r.arduinos.pins[6].digital_state = False

``GPIOPinMode.ANALOGUE_INPUT``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In this mode, we can read the analogue voltage of the pin.

Only pins A0 - A5 support this.

.. code:: python
   
    from sbot import AnaloguePin

   pin_value = r.arduinos.pins[AnaloguePin.A0].analogue_value

Setting the pin mode
--------------------

.. code:: python

   from robot import PinMode

   r.arduino.pins[3].mode = PinMode.INPUT_PULLUP

Analogue pins
-------------

Certain sensors output analogue signals rather than digital ones, and so
have to be read differently. The servo assembly has six analogue inputs,
of which four (analogue pins 4 and 5) are reserved for communication
between the Arduino and the servo shield.

.. Hint:: Analogue signals can have any voltage, while digital
signals can only take on one of two voltages. You can read more about
digital vs analogue signals `here <https://learn.sparkfun.com/tutorials/analog-vs-digital>`__.

To read the value of an analogue pin, call ``read_analogue()`` on the
servo board. This will give you the value of all analogue pins.

.. code:: python

   r.servo_board.read_analogue()["a0"]
   >>> 1.569

.. Hint:: The values are the voltages read on the pins,
   between 0 and 5.

Ultrasound Sensors
------------------

You can also measure distance using an ultrasound sensor from the arduino.

.. code:: python
   
   # TX: 4
   # RX: 5
   u = r.get_ultrasound(4, 5)

   time_taken = u.pulse()

   distance_metres = u.distance()

.. Warning:: If the ultrasound signal never returns, the sensor will timeout and return ``None``.
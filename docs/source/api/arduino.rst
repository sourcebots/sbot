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
from microswitches to LEDs. GPIO is only available on pins 2 to 13 and A0 to A5
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


Setting the pin mode
~~~~~~~~~~~~~~~~~~~~

You will need to ensure that the pin is in the correct pin 
mode before performing an action with that pin. You can read
about the possible pin modes below.

.. code:: python

   r.arduino.pins[3].mode = GPIOPinMode.DIGITAL_INPUT_PULLUP


``GPIOPinMode.DIGITAL_INPUT``
~~~~~~~~~~~~~~~~~

In this mode, the digital state of the pin (whether it is high or low)
can be read.

.. code:: python
   
   r.arduino.pins[4].mode = GPIOPinMode.DIGITAL_INPUT

   pin_value = r.arduino.pins[4].digital_state


``GPIOPinMode.DIGITAL_INPUT_PULLUP``
~~~~~~~~~~~~~~~~~~~~~~~~

Same as ``GPIOPinMode.DIGITAL_INPUT``, but with an internal `pull-up
resistor <https://learn.sparkfun.com/tutorials/pull-up-resistors>`__
enabled.

.. code:: python
   
   r.arduino.pins[4].mode = GPIOPinMode.DIGITAL_INPUT_PULLUP

   pin_value = r.arduino.pins[4].digital_state

``GPIOPinMode.DIGITAL_OUTPUT``
~~~~~~~~~~~~~~~~~~~~~~~

In this mode, we can set binary values of ``0V`` or ``5V`` to the pin.

.. code:: python
   
   r.arduino.pins[4].mode = GPIOPinMode.DIGITAL_OUTPUT
   r.arduino.pins[6].mode = GPIOPinMode.DIGITAL_OUTPUT

   r.arduino.pins[4].digital_state = True
   r.arduino.pins[6].digital_state = False

``GPIOPinMode.ANALOGUE_INPUT``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Certain sensors output analogue signals rather than digital ones, and so
have to be read differently. The arduino has six analogue inputs, which 
are labelled ``A0`` to ``A5``.

.. Hint:: Analogue signals can have any voltage, while digital
signals can only take on one of two voltages. You can read more about
digital vs analogue signals `here <https://learn.sparkfun.com/tutorials/analog-vs-digital>`__.

.. code:: python
   
   from sbot import AnaloguePin

   r.arduino.pins[AnaloguePin.A0].mode = GPIOPinMode.ANALOGUE_INPUT

   pin_value = r.arduino.pins[AnaloguePin.A0].analogue_value

.. Hint:: The values are the voltages read on the pins,
   between 0 and 5.

Ultrasound Sensors
------------------

You can also measure distance using an ultrasound sensor from the arduino.

.. code:: python
   
   # Trigger pin: 4
   # Echo pin: 5
   u = r.arduino.ultrasound_sensors[4, 5]

   time_taken = u.pulse()

   distance_metres = u.distance()

.. Warning:: If the ultrasound signal never returns, the sensor will timeout and return ``None``.

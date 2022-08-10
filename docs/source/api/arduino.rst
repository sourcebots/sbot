Arduino API
===========

The `Arduino <https://store.arduino.cc/arduino-uno-rev3>`__
provides a total of 18 pins for either digital input or output (labelled
2 to 13) and 6 for analogue input (labelled A0 to A5).

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
time, and some pins aren't compatible with certain modes. These pin
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

You will need to ensure that the pin is in the correct pin mode before
performing an action with that pin.

.. code:: python

   r.arduino.pins[3].mode = GPIOPinMode.DIGITAL_INPUT_PULLUP

You can read about the possible pin modes below.


``GPIOPinMode.DIGITAL_INPUT``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In this mode, the digital state of the pin (whether it is high or low)
can be read.

.. code:: python
   
   r.arduino.pins[4].mode = GPIOPinMode.DIGITAL_INPUT

   pin_value = r.arduino.pins[4].digital_read()


``GPIOPinMode.DIGITAL_INPUT_PULLUP``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Same as ``GPIOPinMode.DIGITAL_INPUT``, but with an internal `pull-up
resistor <https://learn.sparkfun.com/tutorials/pull-up-resistors>`__
enabled.

.. code:: python
   
   r.arduino.pins[4].mode = GPIOPinMode.DIGITAL_INPUT_PULLUP

   pin_value = r.arduino.pins[4].digital_read()

``GPIOPinMode.DIGITAL_OUTPUT``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In this mode, you can set binary values of ``0V`` or ``5V`` to the pin.

.. code:: python
   
   r.arduino.pins[4].mode = GPIOPinMode.DIGITAL_OUTPUT
   r.arduino.pins[6].mode = GPIOPinMode.DIGITAL_OUTPUT

   r.arduino.pins[4].digital_write(True)
   r.arduino.pins[6].digital_write(False)

You can get the last value you digitally wrote using ``last_digital_write``.

.. code:: python

    pin_state = r.arduino.pins[4].last_digital_write


``GPIOPinMode.ANALOGUE_INPUT``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Certain sensors output analogue signals rather than digital ones, and so
have to be read differently. The arduino has six analogue inputs, which 
are labelled ``A0`` to ``A5``; however pins ``A4`` and ``A5`` are reserved and cannot be used.

.. Hint:: Analogue signals can have any voltage, while digital
   signals can only take on one of two voltages. You can read more about
   digital vs analogue signals `here <https://learn.sparkfun.com/tutorials/analog-vs-digital>`__.

.. code:: python
   
   from sbot import AnaloguePin

   r.arduino.pins[AnaloguePin.A0].mode = GPIOPinMode.ANALOGUE_INPUT

   pin_value = r.arduino.pins[AnaloguePin.A0].analogue_read()

.. Hint:: The values are the voltages read on the pins,
   between 0 and 5.

.. Warning:: Pins ``A4`` and ``A5`` are reserved and cannot be used.

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

Example
-------

.. code:: python

   from sbot import *
   import time

   r = Robot()


   # Read an infrared sensor connected to pin 2
   infrared_pin = r.arduino.pins[2]
   infrared_pin.mode = GPIOPinMode.DIGITAL_INPUT

   infrared_is_detected = infrared_pin.digital_read()
   if infrared_is_detected:
       print("infrared light detected")
   else:
       print("no infrared light detected")


   # Flash an LED connected to pin 3
   led_pin = r.arduino.pins[3]
   led_pin.mode = GPIOPinMode.DIGITAL_OUTPUT

   led_pin.digital_write(True)
   time.sleep(1)
   led_pin.digital_write(False)


   # Read a potentiometer connected to pin A0
   pot_pin = r.arduino.pins[AnaloguePin.A0]
   pot_pin.mode = GPIOPinMode.ANALOGUE_INPUT

   voltage = pot_pin.analogue_read()
   print(f"potentiometer pin voltage: {voltage}V")


   # Read the distance detected by an ultrasound sensor
   # Trigger on pin 4, echo on pin 5
   sensor = r.arduino.ultrasound_sensors[4, 5]

   pulse_time = sensor.pulse()
   distance = sensor.distance()
   print(f"time taken for pulse to reflect: {pulse_time}")
   print(f"distance to object: {distance}")

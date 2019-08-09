Connecting Your Kit
===================

Essential hardware
------------------

-  Raspberry Pi (the board in a plastic case with many USB ports)
-  Power Board (the board in a plastic case with many green sockets and
   two buttons)
-  Motor Board (the board in a plastic case with three outputs on one end)
-  Servo Board (the board in a plastic case with many pins on the side)
-  Arduino (a board with a metal USB-B connector and a long 30 pin chip)
-  Battery (will be provided later.)
-  USB Hub

Connectors and cables
---------------------

-  2 x 3.81mm CamCon (for the Raspberry Pi)
-  4 x 5mm CamCon (for the Motors)
-  1 x 5mm CamCon with wire loop (attached to the power board)
-  4 x 7.5mm CamCon (for the Motor and Servo Boards)
-  3 x USB-A to micro-USB cables
-  USB-A to USB-B cable (for the Arduino)
-  Wire

Peripherals
-----------

- Servos
- Ultrasound Sensors
- USB Flash Drive

Tools you’ll need
-----------------

-  Pliers
-  Wire Cutters
-  Wire Strippers
-  Screwdriver (2mm flat-head)
-  2 x Motor

You will need to obtain any other needed tools/supplies yourself.

.. Hint:: *CamCons* are the `green connectors </tutorials/kit-assembly.files/camcons.png>`__ 
  used for power wiring within our kit.

Important notes before you start
--------------------------------

.. Warning:: Make sure to read all these **before** you start assembly.

-  Do not disassemble/reassemble your kit without first switching it off
   and unplugging the battery and check it thoroughly before plugging it
   in and switching it on again (don’t be afraid to ask someone to check
   your kit before you do so). If something is connected up incorrectly when
   the kit is powered up, it may damage the components.

-  When wiring CamCons (or anything at all, but CamCons in particular),
   always double-check that the correct connections are made at either
   end (positive to positive, ground to ground, etc.) before plugging in
   the cable or plugging in the battery or switching things on..
   Don’t be afraid to ask someone to check your connections.

-  Colour coding is key; please use *red* for wires connected to
   a powered rail (say 12V or 5V), *black* for wires connected to ground
   (0V rail) and *blue* for motors.

How it all fits together
------------------------

1.  Connect the Raspberry Pi to the Power Board using two 3.81mm CamCons.
    Please make sure that you check the polarity of the connector on the tab.
2.  Connect the USB hub to the Pi by plugging it into any one of its
    four USB sockets.
3.  Connect the Power Board to the Pi via one of the black micro-USB
    cables; the standard USB end goes into any USB socket on the Pi or
    connected USB hub, the micro-USB end into the Power Board.
4.  Connect the Motor Board to the Power Board by screwing the two large
    (7.5mm) CamCons provided onto the opposite ends of a pair of wires,
    ensuring that positive connects to positive and ground to ground,
    and then plugging one end into the appropriate socket of the Motor
    Board and the other into a high power socket (marked ``H0`` or ``H1``) 
    on the side of the  Power Board.
5.  Connect the Motor Board to the Pi by way of another black
    micro-USB cable; the USB A end goes into any USB socket on
    the Pi or connected USB hub, the micro-USB end goes into the Motor
    Board.
6.  Connect the Arduino to the Pi by way of the USB-A to USB-B
    cable; the square-ish USB-B end goes into the appropriate
    metal-cased connector on the Arduino, the standard USB end goes into
    any free USB port on the Pi.

.. Warning:: If the Arduino is not connected directly to the Pi, you may 
   suffer from power stability issues.

7.  Connect the Servo Board to the Power Board by screwing the two large
    (7.5mm) CamCons provided onto the opposite ends of a pair of wires,
    ensuring that positive connects to positive and ground to ground,
    and then plugging one end into the appropriate socket of the Motor
    Board and the other into any socket on the side of the  Power Board.
8.  Connect the Servo Board to the Pi by way of another black
    micro-USB cable; the USB A end goes into any USB socket on
    the Pi or connected USB hub, the micro-USB end goes into the Servo
    Board.

9.  To connect the motors, first screw two medium (5mm) CamCons provided 
    onto the opposite ends of a pair of wires. You can then use this cable
    to connect a motor to the ``M0`` or ``M1`` port on the motor board.

10. To connect a servo, push the three pin connector vertically into the
    pins on the side of the servo board. The black or brown cable (negative)
    should be at the bottom.

11. At this point, check that everything is connected up correctly (it
   may be helpful to ask someone around you to check that all cables
   are connected properly).
12. Connect the Power Board to one of the blue LiPo batteries by
    plugging the yellow connector on the cable connected to the Power
    Board into its counterpart on the battery.
13. If there is not one plugged in already, a loop of wire should be
    connected to the socket beneath the On|Off switch. Check that the
    Power Board works by pressing the On|Off switch and checking that
    the bright LED on the Raspberry Pi comes on green. 

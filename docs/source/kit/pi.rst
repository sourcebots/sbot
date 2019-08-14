Raspberry Pi
============

.. DANGER:: Do not reflash or edit the SD card. This will stop your robot working!

.. figure:: /_static/kit/pi2.jpg
   :alt: Raspberry Pi 3B+
   :scale: 75%

   Raspberry Pi 3B+

The brain of your robot is a Raspberry Pi 3 / 3B+. This handles the running of your python code, recognition of markers and sends control commands to the other boards.

.. Warning:: The model of Pi you have will make no difference to the functioning of your robot.

Power Hat
---------

Your Raspberry Pi has a Pi Power Hat mounted on the top. This allows you to connect power to it using a 3.81mm CamCon.

.. figure:: /_static/kit/power_hat.png
   :alt: Pi Power Hat
   :scale: 50%

   Pi Power Hat

Indicator LEDs
~~~~~~~~~~~~~~

There are 4 indicator LEDs on the Pi Power Hat.

All LEDs will turn on at boot. After the Pi detects a USB stick, the LEDs work as follows:

- 1. This LED will illuminate bright green when your Raspberry Pi is on. You may also notice it flicker during boot.
- 2. This LED will illuminate green when your code has finished without error.
- 3. This LED will illuminate yellow whilst your code is running.
- 4. This LED will illuminate red if your code has crashed.

.. hint:: The LEDs may take a few seconds to update after you insert or remove your USB.

Technical Details
-----------------

Your robot is running a customised version of the Raspbian_ operating system.

When a USB stick is inserted, the SourceBots software will look for a *main.py*, and then execute it.

The output of your code is written to a ``log.txt`` on the USB stick, and also logged to the *systemd journal*.

.. _Raspbian: https://www.raspbian.org/
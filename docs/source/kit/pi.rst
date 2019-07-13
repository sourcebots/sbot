Raspberry Pi
============

.. DANGER:: Do not reflash or edit the SD card. This will stop your robot working!

.. figure:: /_static/kit/pi2.jpg
   :alt: Raspberry Pi 3B+
   :scale: 75%

   Raspberry Pi 3B+

The brain of your robot is a Raspberry Pi 3 / 3B+. This handles the running of your python code, recognition of markers and sends control commands to the other boards.

.. Warning:: The model of Pi you have will make no difference to the functioning of your robot.

Technical Details
-----------------

Your robot is running a customised version of the Raspbian_ operating system.

When a USB stick is inserted, the SourceBots software will look for a *main.py*, and then execute it.

The output of your code is logged to the *systemd journal*, and also written to a file on the USB stick.

.. _Raspbian: https://www.raspbian.org/
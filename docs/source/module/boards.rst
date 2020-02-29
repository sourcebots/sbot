Boards
======

Arduino
-------

.. autoclass:: j5.boards.sb.arduino.SBArduinoBoard
    :members: serial, firmware_version, make_safe, pins

MarkerCamera
------------

.. autoclass:: j5.components.marker_camera.MarkerCamera
    :members: save, see

MotorBoard
----------

.. autoclass:: j5.boards.sr.v4.motor_board.MotorBoard
    :members: serial, firmware_version, make_safe, motors

PowerBoard
----------

.. autoclass:: j5.boards.sr.v4.power_board.PowerBoard
    :members: serial, firmware_version, make_safe, outputs, piezo, start_button, battery_sensor, wait_for_start_flash

ServoBoard
----------

.. autoclass:: j5.boards.sr.v4.servo_board.ServoBoard
    :members: serial, firmware_version, make_safe, servos
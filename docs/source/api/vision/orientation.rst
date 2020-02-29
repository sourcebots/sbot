Orientation
===========

.. figure:: /_static/api/vision/yawpitchroll.png
   :alt: Yaw Pitch and Roll
   :scale: 80%

   Yaw Pitch and Roll (Image source: Peking University)

Orientation represents the rotation of a marker around the x, y, and z axes. These can be accessed as follows:

* ``rot_x`` / ``pitch`` - the angle of rotation in radians counter-clockwise about the Cartesian x axis.
* ``rot_y`` / ``yaw`` - the angle of rotation in radians counter-clockwise about the Cartesian y axis.
* ``rot_z`` / ``roll`` - the angle of rotation in radians counter-clockwise about the Cartesian z axis.

Rotations are applied in order of z, y, x.

.. code:: python

   markers = r.camera.see()

   for m in markers:
       print(m.orientation.rot_x)  # Angle of rotation about x axis.
       print(m.orientation.rot_y)  # Angle of rotation about y axis.
       print(m.orientation.rot_z)  # Angle of rotation about z axis.

.. Note:: In our use case the z axis always faces the camera, and thus will appear as a clockwise rotation

Examples
--------

The following table visually explains what positive and negative rotations represent.

+----------------------------+-----------------------------+
|        0 in all axes       |          |m0x0y0z|          |
+--------------+-------------+---------------+-------------+
| π/4 in rot_x | |m-45x0y0z| | -π/4 in rot_x | |m-45x0y0z| |
+--------------+-------------+---------------+-------------+
| π/4 in rot_y |  |m0x45y0z| | -π/4 in rot_y | |m0x-45y0z| |
+--------------+-------------+---------------+-------------+
| π/4 in rot_z |  |m0x0y45z| | -π/4 in rot_z | |m0x0y-45z| |
+--------------+-------------+---------------+-------------+

.. |m0x0y0z| image:: /_static/api/vision/m0x0y0z.png
    :scale: 30%

.. |m0x0y45z| image:: /_static/api/vision/m0x0y45z.png
    :scale: 30%

.. |m0x0y-45z| image:: /_static/api/vision/m0x0y-45z.png
    :scale: 30%

.. |m0x45y0z| image:: /_static/api/vision/m0x45y0z.png
    :scale: 30%

.. |m0x-45y0z| image:: /_static/api/vision/m0x-45y0z.png
    :scale: 30%

.. |m45x0y0z| image:: /_static/api/vision/m45x0y0z.png
    :scale: 30%

.. |m-45x0y0z| image:: /_static/api/vision/m-45x0y0z.png
    :scale: 30%
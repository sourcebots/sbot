Position
========

Your robot supports three different coordinates systems for position:

* Cartesian
* Spherical
* Cylindrical

The latter are both variants of a `Polar Coordinates system <https://en.wikipedia.org/wiki/Polar_coordinate_system>`_.

Cartesian
---------

This is the coordinates system that you are most likely to be familar with.

.. figure:: /_static/api/vision/cartesian.png
   :alt: The cartesian coordinates system
   :scale: 30%

   The cartesian coordinates system

The cartesian coordinates system has three `principal axes` that are perpendicular to each other.

The value of each coordinate indicates the distance travelled along the axis to the point.

The camera is located at the origin, where the coordinates are ``(0, 0, 0)``.

.. code:: python

   markers = r.camera.see()

   for m in markers:
       print(m.position.cartesian.x)  # Displacement from the origin in metres, along x axis.
       print(m.position.cartesian.y)  # Displacement from the origin in metres, along y axis.
       print(m.position.cartesian.z)  # Displacement from the origin in metres, along z axis.

.. Hint:: The `y` axis decreases as you go up. This matches convention for computer vision systems.

Position
========

Your robot supports three different coordinates systems for position:

* Cartesian
* Spherical

The latter is a `Polar Coordinates system <https://en.wikipedia.org/wiki/Polar_coordinate_system>`_.

Cartesian
---------

.. figure:: /_static/api/vision/cartesian.png
   :alt: The cartesian coordinates system
   :scale: 40%

   The cartesian coordinates system

The `cartesian coordinates system <https://en.wikipedia.org/wiki/Cartesian_coordinate_system>`_ has three
`principal axes` that are perpendicular to each other.

The value of each coordinate indicates the distance travelled along the axis to the point.

The camera is located at the origin, where the coordinates are ``(0, 0, 0)``.

.. code:: python

   markers = r.camera.see()

   for m in markers:
       print(m.cartesian.x)  # Displacement from the origin in millimetres, along x axis.
       print(m.cartesian.y)  # Displacement from the origin in millimetres, along y axis.
       print(m.cartesian.z)  # Displacement from the origin in millimetres, along z axis.

.. Hint:: The `y` axis decreases as you go up. This matches convention for computer vision systems.

Spherical
---------

.. figure:: /_static/api/vision/spherical.png
   :alt: The spherical coordinates system
   :scale: 40%

   The spherical coordinates system

The `spherical coordinates system <https://en.wikipedia.org/wiki/Spherical_coordinate_system>`_ has
three values to specify a specific point in space.

* ``distance`` - The `radial distance`, the distance from the origin to the point, in millimetres.
* ``rot_x`` -  Rotation around the X-axis, in radians, corresponding to `theta` on the diagram.
* ``rot_y`` -  Rotation around the Y-axis, in radians, corresponding to `phi` on the diagram.

The camera is located at the origin, where the coordinates are ``(0, 0, 0)``.

.. code:: python

   markers = r.camera.see()

   for m in markers:
       print(m.spherical.r)  # Distance from the origin in millimetres
       print(m.spherical.theta)  # The angle from the azimuth to the point, in radians.
       print(m.spherical.phi)  # The polar angle from the plane of the camera to the point, in radians.

.. Hint:: You can use the ``math.degrees`` function to convert from radians to degrees.

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
       print(m.position.cartesian.x)  # Displacement from the origin in metres, along x axis.
       print(m.position.cartesian.y)  # Displacement from the origin in metres, along y axis.
       print(m.position.cartesian.z)  # Displacement from the origin in metres, along z axis.

.. Hint:: The `y` axis decreases as you go up. This matches convention for computer vision systems.

Spherical
---------

.. figure:: /_static/api/vision/spherical.png
   :alt: The spherical coordinates system
   :scale: 40%

   The spherical coordinates system

The `spherical coordinates system <https://en.wikipedia.org/wiki/Spherical_coordinate_system>`_ has
three values to specify a specific point in space.

* ``r`` - The `radial distance`, the distance from the origin to the point, in metres.
* ``θ`` (theta) -  The angle from the azimuth to the point, in radians.
* ``φ`` (phi)   -  The polar angle from the plane of the camera to the point, in radians.

The camera is located at the origin, where the coordinates are ``(0, 0, 0)``.

.. code:: python

   markers = r.camera.see()

   for m in markers:
       print(m.position.spherical.r)  # Distance from the origin in metres
       print(m.position.spherical.theta)  # The angle from the azimuth to the point, in radians.
       print(m.position.spherical.phi)  # The polar angle from the plane of the camera to the point, in radians.

.. Hint:: You can use the ``math.degrees`` function to convert from radians to degrees.

.. Note:: When searching for spherical coordinates, you may find a references with phi and theta the other way around.
    This is due to there being *two* conventions for this. We use the ISO 80000-2 16.3 system, as often found in physics.

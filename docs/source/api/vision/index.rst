Vision
======

.. toctree::
   :maxdepth: 1
   :caption: Quick Links:

   orientation
   position

.. figure:: /_static/api/arena_marker.jpg
   :alt: An arena with Fiducial Markers.
   :scale: 30%

   An arena with Fiducial Markers.


Your robot is able to use a webcam to detect `Fiducial Markers <https://en.wikipedia.org/wiki/Fiducial_marker>`__.
Specifically it will detect `AprilTags <https://april.eecs.umich.edu/software/apriltag>`__, using the ``36H11`` marker set.

Using `Pose Estimation <https://en.wikipedia.org/wiki/3D_pose_estimation>`__, it can calculate the orientation and position of
the marker relative to the webcam. Using this data, it is possible to determine the location of your robot and other objects around it.

Searching for markers
---------------------

Assuming you have a webcam connected, you can use ``r.camera.see()`` to take a picture. The software will process the picture
and returns a list of the markers it sees.

.. code:: python

   markers = r.camera.see()

.. Hint:: Your camera will be able to process images better if they are not blurred.

Saving camera output
--------------------

You can also save a snapshot of what your webcam is currently seeing. This can be useful to debug your code.
Every marker that your robot can see will have a square annotated around it, with a red dot indicating the bottom right
corner of the marker. The ID of every marker is also written next to it.

Snapshots are saved to your USB drive, and can be viewed on another computer.

.. code:: python

   r.camera.save("snapshot.jpg")

.. figure:: /_static/api/arena_marker_annotated.jpg
   :alt: An annotated arena with Fiducial Markers.
   :scale: 30%

   An annotated arena with Fiducial Markers.

Markers
-------

The marker objects in the list expose data that may be useful to your robot.

Marker ID
~~~~~~~~~

Every marker has a numeric identifier that can be used to determine what object it represents.

.. code:: python

   markers = r.camera.see()

   for m in markers:
       print(m.id)

Position
~~~~~~~~

Each marker has a position in 3D space, relative to your webcam.

You can access the position using ``m.bearing`` and ``m.distance``.

.. code:: python

   markers = r.camera.see()

   for m in markers:
       print(m.bearing)  # Bearing to the marker from the origin, in radians
       print(m.distance)  # Bearing to the marker from the origin, in radians

For further information on position, including how to use ``m.position`` and the coordinate systems,
see `Position <position.html>`__.

It is also possible to look at the `Orientation <orientation.html>`__ of the marker.

Pixel Positions
~~~~~~~~~~~~~~~

The positions of various points on the marker within the image are exposed over the API. This is useful
if you would like to perform your own Computer Vision calculations.

The corners are specified in clockwise order, starting from the top left corner of the
marker. Pixels are counted from the origin of the image, which
conventionally is in the top left corner of the image.

.. code:: python

   markers = r.camera.see()

   for m in markers:
       print(m.pixel_corners)  # Pixel positions of the marker corners within the image.
       print(m.pixel_centre)  # Pixel positions of the centre of the marker within the image.
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
Every marker that your robot can see will have a square annotated around it, with a red dot indicating the top left
corner of the marker. The ID of every marker is also written next to it.

Snapshots are saved to your USB drive, and can be viewed on another computer.

.. code:: python

   r.camera.save("snapshot.png")

.. figure:: /_static/api/arena_marker_annotated.jpg
   :alt: An annotated arena with Fiducial Markers.
   :scale: 30%

   An annotated arena with Fiducial Markers.
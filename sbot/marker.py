"""Classes for marker detections and various axis representations."""

from math import atan2, hypot
from typing import NamedTuple, Tuple, cast

# import numpy as np
from april_vision import Marker as AprilMarker
from april_vision import Orientation
from numpy.typing import NDArray


class PixelCoordinates(NamedTuple):
    """
    Coordinates within an image made up from pixels.

    Floating point type is used to allow for subpixel detected locations
    to be represented.

    :param float x: X coordinate
    :param float y: Y coordinate
    """

    x: float
    y: float


class Coordinates(NamedTuple):
    """
    3D coordinates in space.

    :param float x: X coordinate
    :param float y: Y coordinate
    :param float z: Z coordinate
    """

    x: float
    y: float
    z: float


class Position(NamedTuple):
    """
    Position of a marker in space from the camera's perspective.

    :param distance:          Distance from the camera to the marker, in millimetres.
    :param horizontal_angle:  Horizontal angle from the camera to the marker, in radians.
                              Ranges from -pi to pi, with positive values indicating
                              markers to the right of the camera. Directly in front
                              of the camera is 0 rad.
    :param vertical_angle:    Vertical angle from the camera to the marker, in radians.
                              Ranges from -pi to pi, with positive values indicating
                              markers above the camera. Directly in front of the camera
                              is 0 rad.
    """

    distance: float
    horizontal_angle: float
    vertical_angle: float


PixelCorners = Tuple[PixelCoordinates, PixelCoordinates, PixelCoordinates, PixelCoordinates]


class Marker(NamedTuple):
    """
    Wrapper of a marker detection with axis and rotation calculated.

    :param id: The ID of the detected marker
    :param size: The physical size of the marker in millimeters
    :param pixel_corners: A tuple of the PixelCoordinates of the marker's corners in the frame
    :param pixel_centre: The PixelCoordinates of the marker's centre in the frame
    :param position: Position information of the marker relative to the camera
    :param orientation: Orientation information of the marker
    """

    id: int
    size: int
    pixel_corners: PixelCorners
    pixel_centre: PixelCoordinates

    position: Position = Position(0, 0, 0)
    orientation: Orientation = Orientation(0, 0, 0)

    @classmethod
    def from_april_vision_marker(cls, marker: AprilMarker) -> 'Marker':
        """Generate a marker object using the data from april_vision's Marker object."""
        if marker.rvec is None or marker.tvec is None:
            raise ValueError("Marker lacks pose information")

        cartesian = cls._standardise_tvec(marker.tvec.flatten())

        return cls(
            id=marker.id,
            size=marker.size,
            pixel_corners=cast(
                PixelCorners,
                tuple(PixelCoordinates(*corner) for corner in marker.pixel_corners)),
            pixel_centre=PixelCoordinates(*marker.pixel_centre),

            position=Position(
                distance=int(hypot(*cartesian) * 1000),
                horizontal_angle=atan2(-cartesian.y, cartesian.x),
                vertical_angle=atan2(cartesian.z, cartesian.x),
            ),

            orientation=Orientation.from_rvec_matrix(marker.rvec),
        )

    @staticmethod
    def _standardise_tvec(tvec: NDArray) -> Coordinates:
        """
        Standardise the tvec to use the marker's coordinate system.

        The marker's coordinate system is defined as:
        - X axis is straight out of the camera
        - Y axis is to the left of the camera
        - Z axis is up
        """
        return Coordinates(tvec[2], -tvec[0], -tvec[1])

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} id={self.id} distance={self.position.distance:.0f}mm "
            f"horizontal_angle={self.position.horizontal_angle:.2f}rad "
            f"vertical_angle={self.position.vertical_angle:.2f}rad size={self.size}mm>"
        )

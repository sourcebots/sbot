"""
Classes for marker detections and various axis representations.
"""
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


PixelCorners = Tuple[PixelCoordinates, PixelCoordinates, PixelCoordinates, PixelCoordinates]


class Marker(NamedTuple):
    """
    Wrapper of a marker detection with axis and rotation calculated.
    """

    id: int
    size: int
    pixel_corners: PixelCorners
    pixel_centre: PixelCoordinates

    # The '2D' distance across the floor
    distance: float = 0
    # In radians, increasing clockwise
    azimuth: float = 0
    # In radians, increasing upwards
    elevation: float = 0

    orientation: Orientation = Orientation(0, 0, 0)

    @classmethod
    def from_april_vision_marker(cls, marker: AprilMarker) -> 'Marker':
        if marker.rvec is None or marker.tvec is None:
            raise ValueError("Marker lacks pose information")

        _cartesian = cls._standardise_tvec(marker.tvec)

        return cls(
            id=marker.id,
            size=marker.size,
            pixel_corners=cast(
                PixelCorners,
                tuple(PixelCoordinates(*corner) for corner in marker.pixel_corners)),
            pixel_centre=PixelCoordinates(*marker.pixel_centre),

            distance=int(hypot(*_cartesian) * 1000),
            azimuth=atan2(-_cartesian.y, _cartesian.x),
            elevation=atan2(_cartesian.z, _cartesian.x),

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
            f"<{self.__class__.__name__} id={self.id} distance={self.distance:.0f}mm "
            f"bearing={self.azimuth:.0f}rad elevation={self.elevation:.0f}rad "
            f"size={self.size}mm>"
        )

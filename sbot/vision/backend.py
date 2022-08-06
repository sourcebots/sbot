"""
SourceBots custom behaviour for Zoloto.

- Determine the size of a marker given the ID
- Determine which OpenCV calibration to use for the currently connected camera.
"""
import logging
from pathlib import Path
from typing import Optional, Tuple

from j5_zoloto import ZolotoHardwareBackend
from zoloto.calibration import parse_calibration_file
from zoloto.cameras import Camera
from zoloto.marker_type import MarkerType

from .game import get_marker_size

LOGGER = logging.getLogger(__name__)


class SBZolotoCamera(Camera):
    """A Zoloto camera that correctly captures markers for SourceBots."""

    def __init__(
            self,
            camera_id: int,
            *,
            marker_size: Optional[int] = None,
            marker_type: MarkerType,
            calibration_file: Optional[Path] = None,
    ) -> None:
        resolution: Optional[Tuple[int, int]] = None
        if calibration_file is not None:
            resolution = parse_calibration_file(calibration_file).resolution

        super().__init__(
            camera_id,
            marker_size=marker_size,
            marker_type=marker_type,
            calibration_file=calibration_file,
            resolution=resolution,
        )

    def get_marker_size(self, marker_id: int) -> int:
        """
        Get the size of a marker given its ID.

        :param marker_id: The offical ID number of the marker.
        :returns: The size of the marker in millimetres.
        """
        return get_marker_size(marker_id)


class SBZolotoHardwareBackend(ZolotoHardwareBackend):
    """A camera backend which automatically finds camera calibration data."""

    camera_class = SBZolotoCamera
    marker_type = MarkerType.APRILTAG_36H11

    def __init__(self, camera_id: int) -> None:
        self._zcam = self.camera_class(
            camera_id,
            marker_type=self.marker_type,
            calibration_file=self.get_calibration_file(),
        )

    def get_calibration_file(self) -> Optional[Path]:
        """Get the calibration file to use."""
        filename = "Logitech C270"
        LOGGER.debug(f"Using {filename} for webcam calibration")
        return Path(__file__).parent / f'calibrations/{filename}.xml'

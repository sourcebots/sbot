"""Vision Camera definitions."""

from pathlib import Path
from typing import Set

from j5.backends.hardware.zoloto.camera_board import (
    ZolotoCameraBoardHardwareBackend,
)
from j5.boards import Board
from zoloto import MarkerDict
from zoloto.cameras import Camera


class SbotCamera(Camera):
    """Camera definition for SourceBots kit."""

    def __init__(self, camera_id: int):

        super().__init__(
            camera_id,
            marker_dict=MarkerDict.DICT_APRILTAG_36H11,
            calibration_file=Path(__file__).parent.joinpath('C270.xml'),
        )

    def get_marker_size(self, marker_id: int) -> int:
        """Get the size of a marker, given it's ID."""
        if marker_id in range(0, 40):
            # WALL_MARKER
            return 250
        else:
            return 100


class SbotCameraBackend(ZolotoCameraBoardHardwareBackend):
    """Camera Backend to override the settings."""

    @classmethod
    def discover(cls) -> Set[Board]:  # type: ignore
        """Discover boards, overriding the parent classes method."""
        return ZolotoCameraBoardHardwareBackend.discover(SbotCamera)

"""An implementation of a camera board using the april_vision library."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Union

from numpy.typing import NDArray

from .internal.board_manager import BoardManager
from .marker import Marker

PathLike = Union[Path, str]
logger = logging.getLogger(__name__)


class Vision:
    """
    Virtual Camera Board for detecting fiducial markers.

    Additionally, it will do pose estimation, along with some calibration
    in order to determine the spatial positon and orientation of the markers
    that it has detected.
    """

    __slots__ = ('_boards',)

    def __init__(self, boards: BoardManager):
        self._boards = boards

    def detect_markers(
        self,
        *,
        frame: NDArray | None = None,
        save: PathLike | None = None
    ) -> list[Marker]:
        """
        Capture an image and identify fiducial markers.

        :param frame: An image to detect markers in, instead of capturing a new one,
        :param save: If given, save the annotated frame to the path.
                     This is given a JPEG extension if none is provided.
        :returns: list of markers that the camera could see.
        """
        cam = self._boards.get_camera()
        if frame is None:
            frame = cam.capture()

        markers = cam.see(frame=frame)

        if save:
            if not frame.flags.writeable:
                frame = frame.copy()
            cam.save(save, frame=frame, detections=markers)
        return [Marker.from_april_vision_marker(marker) for marker in markers]

    def capture(self, save: PathLike | None = None) -> NDArray:
        """
        Get the raw image data from the camera.

        :param save: If given, save the unannotated frame to the path.
                     This is given a JPEG extension if none is provided.
        :returns: Camera pixel data
        """
        cam = self._boards.get_camera()
        raw_frame = cam.capture()
        if save:
            cam.save(save, frame=raw_frame, annotated=False)
        return raw_frame

"""An implementation of a camera board using the april_vision library."""
import logging
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Union

from april_vision import CalibratedCamera, Frame
from april_vision import Marker as AprilMarker
from april_vision import (
    Processor, USBCamera, __version__, calibrations,
    find_cameras, generate_marker_size_mapping,
)
from april_vision.helpers import Base64Sender
from numpy.typing import NDArray

from .marker import Marker
from .utils import Board, BoardIdentity

LOGGER = logging.getLogger(__name__)


class AprilCamera(Board):
    """
    Virtual Camera Board for detecting fiducial markers.

    Additionally, it will do pose estimation, along with some calibration
    in order to determine the spatial positon and orientation of the markers
    that it has detected.

    :param camera_id: The index of the camera to use.
    :param camera_data: The calibration data for the camera.
    :param serial_num: The serial number of the camera.
    """
    __slots__ = ('_serial_num', '_cam')

    @staticmethod
    def get_board_type() -> str:
        """
        Return the type of this board.

        :return: The literal string 'Camera'.
        """
        return 'Camera'

    @classmethod
    def _discover(cls) -> Dict[str, 'AprilCamera']:
        """
        Discover the connected cameras that have calibration data available.

        The calibration data from the april_vision library is included when searching.
        To add additional calibration data, add the paths to the environment variable
        `OPENCV_CALIBRATIONS`, separated by a colon.

        :return: A dict of cameras, keyed by their name and index.
        """
        return {
            (serial := f"{camera_data.name} - {camera_data.index}"):
            cls(camera_data.index, camera_data=camera_data, serial_num=serial)
            for camera_data in find_cameras(calibrations)
        }

    def __init__(self, camera_id: int, camera_data: CalibratedCamera, serial_num: str) -> None:
        # The camera source handles the connection between the camera and the processor
        camera_source = USBCamera.from_calibration_file(
            camera_id,
            calibration_file=camera_data.calibration,
            vidpid=camera_data.vidpid,
        )
        # The processor handles the detection and pose estimation
        self._cam = Processor(
            camera_source,
            calibration=camera_source.calibration,
            name=camera_data.name,
            vidpid=camera_data.vidpid,
            mask_unknown_size_tags=True,
        )
        self._serial_num = serial_num

    def identify(self) -> BoardIdentity:
        """
        Get the identity of the camera.

        The asset tag of the board is the camera name and index.
        The version is the version of the april_vision library.

        :return: The identity of the board.
        """
        return BoardIdentity(
            manufacturer='april_vision',
            board_type='camera',
            asset_tag=self._serial_num,
            sw_version=__version__,
        )

    def close(self) -> None:
        """
        Close the camera.

        The camera will no longer work after this method is called.
        """
        self._cam.close()

    def see(self, *, eager: bool = True, frame: Optional[NDArray] = None) -> List[Marker]:
        """
        Capture an image and identify fiducial markers.

        :param eager: Process the pose estimations of markers immediately,
            currently unused.
        :param frame: An image to detect markers in, instead of capturing a new one,
        :returns: list of markers that the camera could see.
        """
        markers = self._cam.see(frame=frame)
        return [Marker.from_april_vision_marker(marker) for marker in markers]

    def capture(self) -> NDArray:
        """
        Get the raw image data from the camera.

        :returns: Camera pixel data
        """
        return self._cam.capture()

    def save(self, path: Union[Path, str], *, frame: Optional[NDArray] = None) -> None:
        """
        Save an annotated image to a path.

        :param path: The path to save the image to,
            this is given a JPEG extension if none is provided.
        :param frame: An image to annotate and save, instead of capturing a new one,
            defaults to None
        """
        self._cam.save(path, frame=frame)

    def _set_marker_sizes(
        self,
        tag_sizes: Union[float, Dict[int, float]],
    ) -> None:
        """
        Set the size of tags that are used for pose estimation.

        If a dict is given for tag_sizes, only marker IDs that are keys of the
        dict will be detected.

        :param tag_sizes: The size of the tags to use for pose estimation given in meters.
        """
        self._cam.set_marker_sizes(tag_sizes)

    def _set_detection_hook(
        self,
        callback: Callable[[Frame, List[AprilMarker]], None],
    ) -> None:
        """
        Setup a callback to be run after each detection.

        The callback will be passed the frame and the list of markers that were detected.

        :param callback: The function to run after each detection.
        """
        self._cam.detection_hook = callback

    def __repr__(self) -> str:
        return f"<{self.__class__.__qualname__}: {self._serial_num}>"


def _setup_cameras(
    tag_sizes: Dict[Iterable[int], int],
    publish_func: Optional[Callable[[str, bytes], None]] = None,
) -> Dict[str, AprilCamera]:
    """
    Find all connected cameras with calibration and configure tag sizes.

    Optionally set a callback to send a base64 encode JPEG bytestream of each
    image detection is run on.

    :param tag_sizes: The size of the tags to use for pose estimation given in millimeters
    :param publish_func: Optionally, a function to call with the base64 encoded JPEG bytestream
    :return: A dict of cameras, keyed by their name and index.
    """
    # Unroll the tag ID iterables and convert the sizes to meters
    expanded_tag_sizes = generate_marker_size_mapping(tag_sizes)

    if publish_func:
        frame_sender = Base64Sender(publish_func)

    cameras = AprilCamera._discover()

    for camera in cameras.values():
        # Set the tag sizes in the camera
        camera._set_marker_sizes(expanded_tag_sizes)
        if publish_func:
            camera._set_detection_hook(frame_sender.annotated_frame_hook)

    return cameras

"""An implementation of a camera board using the april_vision library."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Union

from april_vision import (
    CalibratedCamera,
    Frame,
    FrameSource,
    Processor,
    USBCamera,
    __version__,
    calibrations,
    find_cameras,
    generate_marker_size_mapping,
)
from april_vision import Marker as AprilMarker
from april_vision.helpers import Base64Sender
from numpy.typing import NDArray

from ..marker import Marker
from .utils import (
    IN_SIMULATOR,
    Board,
    BoardIdentity,
    BoardInfo,
    get_simulator_boards,
)

PathLike = Union[Path, str]
LOGGER = logging.getLogger(__name__)


class AprilCamera(Board):
    """
    Virtual Camera Board for detecting fiducial markers.

    Additionally, it will do pose estimation, along with some calibration
    in order to determine the spatial positon and orientation of the markers
    that it has detected.

    :param camera_source: The source of the camera frames.
    :param calibration: The intrinsic calibration of the camera.
    :param serial_num: The serial number of the camera.
    :param name: The name of the camera.
    :param vidpid: The VID:PID of the camera.
    """

    __slots__ = ('_cam', '_serial_num')

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
        if IN_SIMULATOR:
            return {
                camera_info.serial_number: cls.from_webots_camera(camera_info)
                for camera_info in get_simulator_boards('CameraBoard')
            }

        return {
            (serial := f"{camera_data.name} - {camera_data.index}"):
            cls.from_id(camera_data.index, camera_data=camera_data, serial_num=serial)
            for camera_data in find_cameras(calibrations)
        }

    def __init__(
        self, camera_source: FrameSource,
        calibration: tuple[float, float, float, float] | None,
        serial_num: str,
        name: str,
        vidpid: str = "",
    ) -> None:
        # The processor handles the detection and pose estimation
        self._cam = Processor(
            camera_source,
            calibration=calibration,
            name=name,
            vidpid=vidpid,
            mask_unknown_size_tags=True,
        )
        self._serial_num = serial_num

    @classmethod
    def from_webots_camera(cls, camera_info: BoardInfo) -> 'AprilCamera':
        """
        Create a camera from a webots camera.

        :param camera_info: The information about the virtual camera,
                            including the url to connect to.
        :return: The camera object.
        """
        from sbot.simulator.camera import WebotsRemoteCameraSource

        camera_source = WebotsRemoteCameraSource(camera_info)
        return cls(
            camera_source,
            calibration=camera_source.calibration,
            serial_num=camera_info.serial_number,
            name=camera_info.serial_number,
        )

    @classmethod
    def from_id(
        cls,
        camera_id: int,
        camera_data: CalibratedCamera,
        serial_num: str,
    ) -> 'AprilCamera':
        """
        Create a camera from an ID.

        :param camera_id: The ID of the camera to create.
        :param camera_data: The calibration data for the camera.
        :param serial_num: The serial number of the camera.
        :return: The camera object.
        """
        # The camera source handles the connection between the camera and the processor
        camera_source = USBCamera.from_calibration_file(
            camera_id,
            calibration_file=camera_data.calibration,
            vidpid=camera_data.vidpid,
        )
        return cls(
            camera_source,
            calibration=camera_source.calibration,
            serial_num=serial_num,
            name=camera_data.name,
            vidpid=camera_data.vidpid,
        )

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

    def see(
        self,
        *,
        frame: Union[NDArray, None] = None,
        save: Union[PathLike, None] = None,
    ) -> List[Marker]:
        """
        Capture an image and identify fiducial markers.

        :param frame: An image to detect markers in, instead of capturing a new one,
        :param save: If given, save the annotated frame to the path.
                     This is given a JPEG extension if none is provided.
        :returns: list of markers that the camera could see.
        """
        if frame is None:
            frame = self._cam.capture()

        markers = self._cam.see(frame=frame)

        if save:
            if not frame.flags.writeable:
                frame = frame.copy()
            self._cam.save(save, frame=frame, detections=markers)
        return [Marker.from_april_vision_marker(marker) for marker in markers]

    def capture(self, *, save: Union[PathLike, None] = None) -> NDArray:
        """
        Get the raw image data from the camera.

        :param save: If given, save the unannotated frame to the path.
                     This is given a JPEG extension if none is provided.
        :returns: Camera pixel data
        """
        raw_frame = self._cam.capture()
        if save:
            self._cam.save(save, frame=raw_frame, annotated=False)
        return raw_frame

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

    cameras = AprilCamera._discover()  # noqa: SLF001

    for camera in cameras.values():
        # Set the tag sizes in the camera
        camera._set_marker_sizes(expanded_tag_sizes)  # noqa: SLF001
        if publish_func:
            camera._set_detection_hook(frame_sender.annotated_frame_hook)  # noqa: SLF001

    return cameras

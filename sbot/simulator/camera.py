"""A virtual frame source for a camera connected over a socket connection."""

import struct

import cv2
import numpy as np
from april_vision import FrameSource
from numpy.typing import NDArray
from serial import serial_for_url

from ..internal.utils import BoardInfo

HEADER_SIZE = 5  # 1 byte for the type, 4 bytes for the length
IMAGE_TAG_ID = 0


class WebotsRemoteCameraSource(FrameSource):
    """
    A virtual frame source for a camera connected to a Webots robot.

    This class communicates with the camera over a socket connection.
    Both the calibration data and the image data is read over this socket.

    :param camera_info: The information about the camera to connect to.
    """

    # Webots cameras include an alpha channel, this informs april_vision of how to handle it
    COLOURSPACE = cv2.COLOR_BGRA2GRAY

    def __init__(self, camera_info: BoardInfo) -> None:
        self.calibration = (0.0, 0.0, 0.0, 0.0)
        # Use pyserial to give a nicer interface for connecting to the camera socket
        self._serial = serial_for_url(camera_info.url, baudrate=115200, timeout=None)

        # Check the camera is connected
        response = self._make_request("*IDN?")
        if not response.split(b":")[1].lower().startswith(b"cam"):
            raise RuntimeError(f"Camera not connected to a camera, returned: {response!r}")

        # Get the calibration data for this camera
        response = self._make_request("CAM:CALIBRATION?")

        # The calibration data is returned as a string of floats separated by colons
        new_calibration = tuple(map(float, response.split(b":")))
        assert len(new_calibration) == 4, f"Invalid calibration data: {new_calibration}"
        self.calibration = new_calibration

        # Get the image size for this camera
        response = self._make_request("CAM:RESOLUTION?")
        self.image_size = tuple(map(int, response.split(b":")))
        assert len(self.image_size) == 2, f"Invalid image dimensions: {self.image_size}"

    def read(self, fresh: bool = True) -> NDArray:
        """
        The method for getting a new frame.

        :param fresh: Whether to flush the device's buffer before capturing
        the frame, unused.
        """
        self._serial.write(b"CAM:FRAME!\n")
        # The image is encoded as a TLV (Type, Length, Value) packet
        # so we need to read the header to get the type and length of the image
        header = self._serial.read(HEADER_SIZE)
        assert len(header) == HEADER_SIZE, f"Invalid header length: {len(header)}"
        img_tag, img_len = struct.unpack('>BI', header)
        assert img_tag == IMAGE_TAG_ID, f"Invalid image tag: {img_tag}"

        # Get the image data now we know the length
        img_data = self._serial.read(img_len)
        assert len(img_data) == img_len, f"Invalid image data length: {len(img_data)}"

        rgb_frame_raw: NDArray[np.uint8] = np.frombuffer(img_data, np.uint8)

        # Height is first, then width, then channels
        return rgb_frame_raw.reshape((self.image_size[1], self.image_size[0], 4))

    def close(self) -> None:
        """Close the underlying socket on exit."""
        self._serial.close()

    def _make_request(self, command: str) -> bytes:
        self._serial.write(command.encode() + b"\n")
        response = self._serial.readline()
        if not response.endswith(b"\n") or response.startswith(b"NACK:"):
            raise RuntimeError(f"Failed to communicate with camera, returned: {response!r}")
        return response

"""
BoardManager class for managing boards connected to the robot.

This is the central class for managing the boards connected to the robot.
It is responsible for discovering connected boards, loading them, and
managing their outputs.
"""
from __future__ import annotations

import atexit
import enum
import logging
import os
from typing import Callable, ClassVar, NamedTuple

from april_vision import (
    FrameSource,
    USBCamera,
    calibrations,
    find_cameras,
    generate_marker_size_mapping,
)
from april_vision import Processor as AprilCamera
from april_vision.helpers import Base64Sender
from serial.tools.list_ports import comports
from serial.tools.list_ports_common import ListPortInfo

from sbot.game_specific import MARKER_SIZES

from .exceptions import BoardDisconnectionError
from .serial_wrapper import BASE_TIMEOUT, SerialWrapper
from .utils import BoardIdentity, get_simulator_boards, get_USB_identity

try:
    from .mqtt import MQTT_VALID, MQTTClient, get_mqtt_variables
except ImportError:
    MQTT_VALID = False


from .overrides import get_overrides

logger = logging.getLogger(__name__)
IN_SIMULATOR = os.environ.get('WEBOTS_SIMULATOR', '') == '1'


class _DiscoveryMode(enum.Enum):
    """The mode in which to discover boards."""

    NORMAL = enum.auto()
    SIMULATOR = enum.auto()
    MANUAL = enum.auto()


class OutputIdentifier(NamedTuple):
    """
    An identifier for a single output on a board.

    :param port: The SerialWrapper object that is connected to the board.
    :param idx: The index of the output on the board.
    """

    port: SerialWrapper
    idx: int


class DiscoveryTemplate(NamedTuple):
    """
    A template for the board discovery function.

    :param identifier: The identifier that will be used to access discovered
        boards of this type.
    :param name: The name of the board type, this is used in logging and error messages.
    :param vid: The USB vendor ID of the board.
    :param pid: The USB product ID of the board.
    :param board_type: The identifier returned by the board's identity query.
    :param num_outputs: The number of outputs on the board.
    :param baud_rate: The baud rate to use when connecting to the board.
    :param cleanup: A function to call when the board is disconnected.
    :param max_boards: The maximum number of boards of this type that can be connected.
    :param delay_after_connect: The delay to wait after connecting to the board before sending
        commands, this is necessary devices that reset when the serial port is opened.
    :param use_usb_serial: If True, the asset tag from the USB serial number will be used as
        the asset tag for the board, this is necessary for some boards that do not have the
        asset tag available in the firmware.
    :param sim_board_type: The board type to match when in simulator mode.
    :param sim_only: If True, this board type will only be discovered in simulator mode.
    """

    identifier: str
    name: str
    vid: int
    pid: int
    board_type: str
    num_outputs: int = 0
    baud_rate: int = 115200
    setup: Callable[[SerialWrapper], None] | None = None
    cleanup: Callable[[SerialWrapper], None] | None = None
    max_boards: int | None = None
    delay_after_connect: int = 0
    use_usb_serial: bool = False
    sim_board_type: str | None = None
    sim_only: bool = False
    timeout: float | None = BASE_TIMEOUT


class PortIdentity(NamedTuple):
    """
    The information known about a serial port.

    :param device: The device name of the port, e.g. "/dev/ttyUSB0".
    :param serial_number: The serial number of the device, if available.
    :param raw_port: The raw ListPortInfo object for the port.
    """

    device: str
    serial_number: str = ""
    raw_port: ListPortInfo | None = None


class BoardManager:
    """
    Manages the boards connected to the robot.

    Each type of board must be registered with the BoardManager before it can be
    discovered. This is done by passing a BoardTemplate to the register_board
    method.
    """

    _regisered_templates: ClassVar[list[DiscoveryTemplate]] = []

    def __init__(self) -> None:
        self._loaded: bool = False
        self.boards: dict[str, dict[str, SerialWrapper]] = {}
        self.outputs: dict[str, list[OutputIdentifier]] = {}
        self.cameras: dict[str, AprilCamera] = {}
        self.init_mqtt()

    @classmethod
    def register_board(cls, board: DiscoveryTemplate) -> None:
        """
        Register a board template with the BoardManager.

        The template will be used to identify boards of the given type when
        discovering connected boards.
        """
        assert isinstance(board, DiscoveryTemplate), "board must be a BoardTemplate"
        cls._regisered_templates.append(board)

    def load_boards(self) -> None:
        """
        Load all connected boards.

        This method will attempt to identify all connected boards and load them
        into the boards dictionary. It will also sort the lists by the board
        index.
        """
        if self.loaded:
            raise RuntimeError("Boards have already been loaded")

        # Prepare the boards dictionary so every board key exists
        for template in self._regisered_templates:
            self.boards[template.identifier] = {}

        if not IN_SIMULATOR:
            # Load power boards first and enable all outputs
            power_template = next(
                filter(lambda x: x.identifier == 'power', self._regisered_templates),
            )
            for port in comports():
                if not (port.vid == power_template.vid and port.pid == power_template.pid):
                    continue
                port_data = PortIdentity(port.device, port.serial_number or "", port)
                if not self._inititalse_port(port_data, power_template, _DiscoveryMode.NORMAL):
                    logger.debug(
                        f"Found power board at {port.device!r}, "
                        "but it could not be identified. Ignoring this device"
                    )

            if power_template.setup is not None:
                for board in self.boards['power'].values():
                    # Enable all outputs on the power board
                    power_template.setup(board)

            # Do normal (USB) board loading
            for port in comports():
                port_data = PortIdentity(port.device, port.serial_number or "", port)
                possible_boards = filter(
                    lambda x: (
                        x.sim_only is False
                        and x.vid == port.vid
                        and x.pid == port.pid
                    ),
                    self._regisered_templates
                )
                for template in possible_boards:
                    if self._inititalse_port(port_data, template, _DiscoveryMode.NORMAL):
                        break
                else:
                    logger.debug(
                        f"Found serial port at {port.device!r}, "
                        "but it could not be identified. Ignoring this device"
                    )
        else:
            # Do simulator board loading
            for board_info in get_simulator_boards():
                if board_info.type_str == 'CameraBoard':
                    # Cameras are loaded separately
                    continue

                port_data = PortIdentity(board_info.url, board_info.serial_number)
                possible_boards = filter(
                    lambda x: (
                        x.sim_board_type is not None
                        and x.sim_board_type == board_info.type_str
                    ),
                    self._regisered_templates
                )
                for template in possible_boards:
                    if self._inititalse_port(port_data, template, _DiscoveryMode.SIMULATOR):
                        break
                else:
                    logger.debug(
                        f"Simulator specified {board_info.type_str} at port "
                        f"{board_info.url!r}, did not match any registered boards. "
                        "Ignoring this device"
                    )

        overrides = get_overrides()

        # Do manual board loading, get list of ports from overrides
        for template in self._regisered_templates:
            board_type = template.identifier.upper()
            manual_port_str = overrides.get(f'MANUAL_{board_type}_PORTS') or ""
            if not manual_port_str:
                continue

            manual_ports = manual_port_str.split(',')
            for port_str in manual_ports:
                port_data = PortIdentity(port_str)
                if not self._inititalse_port(port_data, template, _DiscoveryMode.MANUAL):
                    logger.warning(
                        f"Failed ot connect to manually specified {template.name} at port "
                        f"{port_str!r}, ignoring this device"
                    )

        # Run startup commands on all boards
        for template in self._regisered_templates:
            if not IN_SIMULATOR and template.identifier == 'power':
                # Power boards have already been setup
                continue
            for board in self.boards[template.identifier].values():
                if template.setup is not None:
                    template.setup(board)

        # Sort boards by asset tag
        for board_type in self.boards.keys():
            sort_override = overrides.get(f'SORT_{board_type.upper()}_ORDER') or ""
            if sort_override:
                self._custom_sort(board_type, sort_override.split(','))
            else:
                self._custom_sort(board_type, [])

        self._loaded = True

        # Validate max board limits
        for template in self._regisered_templates:
            if (
                template.max_boards is not None
                and len(self.boards[template.identifier]) > template.max_boards
            ):
                raise RuntimeError(
                    f"This system is configured to only support up to "
                    f"{template.max_boards} {template.name} boards, but "
                    f"{len(self.boards[template.identifier])} were found"
                )

    def populate_outputs(self) -> None:
        """
        Populate the outputs dictionary with all outputs on the connected boards.

        Boards must be loaded before calling this method.

        This method will populate the outputs dictionary with a list of
        OutputIdentifiers for each output on each board.
        """
        if not self.loaded:
            raise RuntimeError("Boards have not been loaded")

        for template in self._regisered_templates:
            self.outputs[template.identifier] = []
            for board in self.boards[template.identifier].values():
                for idx in range(template.num_outputs):
                    self.outputs[template.identifier].append(OutputIdentifier(board, idx))

    @property
    def loaded(self) -> bool:
        """Return True if the boards have been loaded."""
        return self._loaded

    def _inititalse_port(
        self,
        port: PortIdentity,
        template: DiscoveryTemplate,
        mode: _DiscoveryMode = _DiscoveryMode.NORMAL,
    ) -> bool:
        """
        Initialise a serial port.

        This method will attempt to identify the board connected to the given
        serial port and load it into the boards dictionary.
        """
        if mode == _DiscoveryMode.NORMAL:
            # Create board identity from USB port info
            assert isinstance(port.raw_port, ListPortInfo), \
                "raw_port must be populated for NORMAL discovery mode"
            initial_identity = get_USB_identity(port.raw_port)
        elif mode == _DiscoveryMode.SIMULATOR:
            initial_identity = BoardIdentity(
                manufacturer='sbot_simulator',
                board_type=template.board_type,
                asset_tag=port.serial_number,
            )
        else:  # DiscoveryMode.MANUAL
            initial_identity = BoardIdentity(
                board_type='manual',
                asset_tag=port.serial_number,
            )

        board_serial = SerialWrapper(
            port.device,
            template.baud_rate,
            identity=initial_identity,
            delay_after_connect=template.delay_after_connect,
            timeout=template.timeout,
        )
        try:
            response = board_serial.query('*IDN?')
        except BoardDisconnectionError:
            if mode == _DiscoveryMode.NORMAL:
                err_msg = (
                    f"Found {template.name}-like serial port at {port.device!r}, "
                    "but it could not be identified. Ignoring this device"
                )
            elif mode == _DiscoveryMode.SIMULATOR:
                err_msg = (
                    f"Simulator specified {template.name} at port {port.device!r}, "
                    "could not be identified. Ignoring this device"
                )
            else:  # DiscoveryMode.MANUAL
                err_msg = (
                    f"Manually specified {template.name} at port {port.device!r}, "
                    "could not be identified. Ignoring this device"
                )

            logger.warning(err_msg)
            return False

        identity = BoardIdentity(*response.split(':'))
        if template.use_usb_serial:
            prev_identity = identity._asdict()
            prev_identity['asset_tag'] = initial_identity.asset_tag
            identity = BoardIdentity(**prev_identity)

        if identity.board_type != template.board_type:
            logger.warning(
                f"Board returned type {identity.board_type!r}, "
                f"expected {template.board_type!r}. Ignoring this device")
            return False
        board_serial.set_identity(identity)

        self.boards[template.identifier][identity.asset_tag] = board_serial

        if template.cleanup is not None:
            atexit.register(template.cleanup, board_serial)

        return True

    def _custom_sort(self, identifier: str, sort_order: list[str]) -> None:
        """
        Sort the boards for a given identifier, supports using a custom sort order.

        :param identifier: The identifier of the boards to sort.
        :param sort_order: The custom sort order to use, if empty the boards will be sorted
            by asset tag.
        :raises RuntimeError: If extra boards are found for the identifier when using a custom
            sort order.
        """
        boards = self.boards[identifier]

        if len(sort_order) == 0:
            boards_sorted = dict(sorted(boards.items()))
        else:
            # Use custom sort order
            extra_boards = set(boards.keys()) - set(sort_order)
            if extra_boards:
                raise RuntimeError(
                    f"Extra boards found for {identifier}: {', '.join(extra_boards)}."
                    "Cannot use custom sort order"
                )

            boards_sorted = {
                asset_tag: boards[asset_tag]
                for asset_tag in sort_order
                if asset_tag in boards.keys()
            }

        self.boards[identifier] = boards_sorted

    def find_output(self, identifier: str, idx: int) -> OutputIdentifier:
        """
        Find an output on a board.

        :param identifier: The identifier of the board.
        :param idx: The index of the output on the board.
        :return: The OutputIdentifier for the output.
        :raises ValueError: If the output does not exist on the board.
        :raises KeyError: If no board with the given identifier is registered.
        """
        try:
            return self.outputs[identifier][idx]
        except IndexError:
            name = self._name_from_identifier(identifier)
            raise ValueError(f"Output {idx} does not exist on {name}")
        except KeyError:
            raise KeyError(f"No board with identifier {identifier!r}")

    def get_boards(self, identifier: str) -> dict[str, SerialWrapper]:
        """
        Get all boards of a given type.

        :param identifier: The identifier of the board type.
        :return: A dictionary of asset tags to SerialWrapper objects.
        :raises KeyError: If no board with the given identifier is registered.
        """
        try:
            return self.boards[identifier]
        except KeyError:
            raise KeyError(f"No board with identifier {identifier!r}")

    def get_first_board(self, identifier: str) -> SerialWrapper:
        """
        Get the first board of a given type.

        :param identifier: The identifier of the board type.
        :return: The SerialWrapper object for the first board.
        :raises KeyError: If no board with the given identifier is registered.
        :raises ValueError: If no boards of the given type are connected.
        """
        try:
            return next(iter(self.boards[identifier].values()))
        except KeyError:
            raise KeyError(f"No board with identifier {identifier!r}") from None
        except StopIteration:
            name = self._name_from_identifier(identifier)
            raise ValueError(f"No {name}s connected") from None

    def _name_from_identifier(self, identifier: str) -> str:
        for template in self._regisered_templates:
            if template.identifier == identifier:
                return template.name
        return identifier

    def init_mqtt(self) -> None:
        """Initialise the MQTT connection."""
        if MQTT_VALID:
            self.mqtt: MQTTClient | None = None
            # get the config from env vars
            mqtt_config = get_mqtt_variables()
            self.mqtt = MQTTClient.establish(**mqtt_config)
        else:
            self.mqtt = None

    def load_cameras(self) -> None:
        """
        Find all connected cameras with calibration and configure tag sizes.

        Where MQTT is enabled, set up a frame sender to send annotated frames
        as base64 encoded JPEG bytestreams of each image, detection is run on.

        This method will attempt to identify all connected cameras and load them
        into the cameras dictionary. Cameras will be indexed by their name.
        """
        if self.cameras:
            raise RuntimeError("Cameras have already been loaded")

        camera_source: FrameSource
        # Unroll the tag ID iterables and convert the sizes to meters
        expanded_tag_sizes = generate_marker_size_mapping(MARKER_SIZES)

        if MQTT_VALID and self.mqtt:
            frame_sender = Base64Sender(self.mqtt.wrapped_publish)
        else:
            frame_sender = None

        if IN_SIMULATOR:
            from sbot.simulator.camera import WebotsRemoteCameraSource

            for camera_info in get_simulator_boards('CameraBoard'):
                camera_source = WebotsRemoteCameraSource(camera_info)
                # The processor handles the detection and pose estimation
                camera = AprilCamera(
                    camera_source,
                    calibration=camera_source.calibration,
                    name=camera_info.serial_number,
                    mask_unknown_size_tags=True,
                )

                # Set the tag sizes in the camera
                camera.set_marker_sizes(expanded_tag_sizes)

                if frame_sender:
                    camera.detection_hook = frame_sender.annotated_frame_hook

                self.cameras[camera_info.serial_number] = camera
        else:
            for camera_data in find_cameras(calibrations):
                cam_name = f"{camera_data.name} - {camera_data.index}"

                # The camera source handles the connection between the camera and the processor
                camera_source = USBCamera.from_calibration_file(
                    camera_data.index,
                    calibration_file=camera_data.calibration,
                    vidpid=camera_data.vidpid,
                )
                # The processor handles the detection and pose estimation
                camera = AprilCamera(
                    camera_source,
                    calibration=camera_source.calibration,
                    name=camera_data.name,
                    vidpid=camera_data.vidpid,
                    mask_unknown_size_tags=True,
                )

                # Set the tag sizes in the camera
                camera.set_marker_sizes(expanded_tag_sizes)

                if frame_sender:
                    camera.detection_hook = frame_sender.annotated_frame_hook

                self.cameras[cam_name] = camera

    def get_camera(self) -> AprilCamera:
        """Get the first camera connected to the robot."""
        if len(self.cameras) > 1:
            camera_name = next(iter(self.cameras.keys()))
            logger.warning(f"Multiple cameras connected, using {camera_name!r}")

        try:
            return next(iter(self.cameras.values()))
        except StopIteration:
            raise ValueError("No cameras connected") from None

    def log_connected_boards(self, show_output_map: bool = False) -> None:
        """
        Log the board types and serial numbers of all the boards connected to the robot.

        Firmware versions are also logged at debug level.
        """
        seen_identifiers: set[str] = set()
        if show_output_map:
            for template in self._regisered_templates:
                if template.identifier in seen_identifiers:
                    # Dedup template identifiers
                    continue
                seen_identifiers.add(template.identifier)
                board_name = self._name_from_identifier(template.identifier)
                board_outputs = self.outputs[template.identifier]
                num_outputs = template.num_outputs
                # Generate the mapping from the outputs to asset tags and ports on each board
                if num_outputs == 0:
                    for asset_tag in self.boards[template.identifier].keys():
                        logger.info(f"Connected {board_name}, serial: {asset_tag}")
                else:
                    output_map = {
                        idx: (port.identity.asset_tag, port_idx)
                        for idx, (port, port_idx) in enumerate(board_outputs)
                    }
                    if not output_map:
                        # No outputs found
                        continue

                    output_boards = self.boards[template.identifier]
                    logger.info(f"Connected {len(output_boards)} {board_name}s")
                    for idx, (asset_tag, output_idx) in output_map.items():
                        logger.info(
                            f"Index: {idx}  =>  serial: {asset_tag}, output {output_idx}"
                        )

        for board_type, boards in self.boards.items():
            board_name = self._name_from_identifier(board_type)
            for asset_tag, board in boards.items():
                if not show_output_map:
                    logger.info(f"Connected {board_name}, serial: {asset_tag}")

                # Always log the firmware version of each board
                logger.debug(
                    f"Firmware version of "
                    f"{asset_tag}: {board.identity.sw_version}, "
                    f"reported type: {board.identity.board_type}, "
                    f"port: {board.serial.port}, "
                )

        # Log cameras
        if self.cameras:
            camera_names = ', '.join(self.cameras.keys())
            if len(self.cameras) > 1:
                logger.info(
                    f"Connected cameras: {camera_names}, "
                    f"using {next(iter(self.cameras.keys()))}"
                )
            else:
                logger.info(f"Connected camera: {camera_names}")
        else:
            logger.info("No cameras connected")

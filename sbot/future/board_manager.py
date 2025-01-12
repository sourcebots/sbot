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

from sbot.exceptions import BoardDisconnectionError
from sbot.serial_wrapper import SerialWrapper
from sbot.utils import BoardIdentity, get_simulator_boards, get_USB_identity
from serial.tools.list_ports import comports
from serial.tools.list_ports_common import ListPortInfo

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
    cleanup: Callable[[SerialWrapper], None] | None = None
    max_boards: int | None = None
    delay_after_connect: int = 0
    use_usb_serial: bool = False
    sim_board_type: str | None = None
    sim_only: bool = False


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
            manual_port_str = overrides.get(f'MANUAL_{template.identifier}_PORTS') or ""
            manual_ports = manual_port_str.split(',')
            for port_str in manual_ports:
                port_data = PortIdentity(port_str)
                if not self._inititalse_port(port_data, template, _DiscoveryMode.MANUAL):
                    logger.warning(
                        f"Failed ot connect to manually specified {template.name} at port "
                        f"{port_str!r}, ignoring this device"
                    )

        # Sort boards by asset tag
        for board_type in self.boards.keys():
            sort_override = overrides.get(f'SORT_{board_type}_ORDER') or ""
            self._custom_sort(board_type, sort_override.split(','))

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
            identity = BoardIdentity(
                **identity._asdict(),
                asset_tag=initial_identity.asset_tag,
            )

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

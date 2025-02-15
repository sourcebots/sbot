from __future__ import annotations

import pytest

from os import environ

# Disable trying to run any discovery or robot code when sbot is imported
environ['SBOT_PYTEST'] = '1'
environ.pop('SBOT_MQTT_URL', None)

from sbot.internal.utils import BoardIdentity
from sbot.internal.board_manager import BoardManager


def pytest_addoption(parser):
    parser.addoption(
        "--hardware",
        action="store_true",
        help="Run hardware-in-the-loop tests.",
    )


def pytest_runtest_setup(item):
    if item.config.getoption("--hardware"):
        # Run hardware tests
        if 'hardware' not in item.keywords:
            pytest.skip("skipping non-hardware test")
    else:
        # Run unit tests
        if 'hardware' in item.keywords:
            pytest.skip("test requires physical boards connected and --hardware")


class MockSerialWrapper:
    """
    A class that mocks the sbot.internal.serial_wrapper.SerialWrapper class.

    Takes a list of 2-tuples of request and response strings.
    Asserts that each request is sent in order and returns the matching response.

    Implements the same interface as sbot.internal.serial_wrapper.SerialWrapper.
    """

    def __init__(self, responses: list[tuple[str, str]]) -> None:
        """Initialize the mock with a list of responses."""
        self.responses = responses
        self.request_index = 0
        self.identity = BoardIdentity()

    def _add_responses(self, responses: list[tuple[str, str]]) -> None:
        """Add more responses to the end of the list."""
        self.responses.extend(responses)

    def __call__(
        self,
        port: str,
        baud: int,
        timeout: float = 0.5,
        identity: BoardIdentity = BoardIdentity(),
        delay_after_connect: float = 0,
    ) -> 'MockSerialWrapper':
        """This will replace the original init method during the test."""
        self._port = port
        self._baudrate = baud
        return self

    def query(self, request: str) -> str:
        """
        Mocks sending a command and returning the response.

        Asserts that the request is the next one in the list of expected requests.
        """
        # Assert that we have not run out of responses
        # and that the request is the next one we expect
        assert self.request_index < len(self.responses), f"Unexpected request: {request}"
        assert request == self.responses[self.request_index][0]

        # Fetch the response and increment the request index
        response = self.responses[self.request_index][1]
        self.request_index += 1
        return response

    def write(self, request: str) -> None:
        """Send a command without waiting for a response."""
        _ = self.query(request)

    def set_identity(self, identity: BoardIdentity) -> None:
        """Set the identity of the board."""
        self.identity = identity


class MockAtExit:
    def __init__(self):
        self._callbacks = []

    def register(self, callback):
        self._callbacks.append(callback)

    def unregister(self, callback):
        try:
            self._callbacks.remove(callback)
        except ValueError:
            pass

def setup_mock_board_manager():
    board_manager = BoardManager()
    board_manager._loaded = True

    def preload_boards(self):
        # Prepare the boards dictionary so every board key exists
        for template in self._regisered_templates:
            self.boards[template.identifier] = {}

    board_manager.preload_boards = preload_boards

    return board_manager

import logging

import pytest

from sbot.internal.exceptions import BoardDisconnectionError
from sbot.internal.serial_wrapper import SerialWrapper, retry
from sbot.internal.utils import BoardIdentity


def test_retry_exception() -> None:
    """Test the retry decorator when an exception is repeatedly raised."""
    call_count = 0

    @retry(times=3, exceptions=Exception)
    def test_func() -> None:
        """Test function."""
        nonlocal call_count
        call_count += 1
        raise Exception("Test exception")

    with pytest.raises(Exception):
        test_func()

    # 4 calls for 3 retries
    assert call_count == 4


def test_retry_no_exception() -> None:
    """Test the retry decorator when no exception is raised."""
    call_count = 0

    @retry(times=3, exceptions=Exception)
    def test_func() -> None:
        """Test function."""
        nonlocal call_count
        call_count += 1
        return 'Test return'

    assert test_func() == 'Test return'

    # 1 call for no retries
    assert call_count == 1


def test_retry_single_exception() -> None:
    """Test the retry decorator."""
    call_count = 0

    @retry(times=3, exceptions=Exception)
    def test_func() -> None:
        """Test function."""
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # Only throw an execption on the first call
            raise Exception("Test exception")
        return 'Test return'

    assert test_func() == 'Test return'

    # only first call raises an exception
    assert call_count == 2


def test_serial_wrapper(caplog) -> None:
    """
    Test the serial wrapper.

    Using a loopback serial port causes all data to be sent back to the sender.
    """
    # Capture all logging
    caplog.set_level(0)
    serial_wrapper = SerialWrapper(
        port='loop://',
        baud=115200,
        identity=BoardIdentity(
            board_type='Test board',
            sw_version='1.0',
            asset_tag='1234',
        ),
    )

    # Test that the serial port uses the correct identity
    assert str(serial_wrapper) == "<SerialWrapper 'loop://' '1234'>"

    # Test that we can set a new identity
    serial_wrapper.identity = BoardIdentity(
        board_type='Test board',
        sw_version='1.0',
        asset_tag='5678',
    )
    assert str(serial_wrapper) == "<SerialWrapper 'loop://' '5678'>"

    # Test that the serial port is opened on the first message
    assert not serial_wrapper.serial.is_open
    assert serial_wrapper.query("Echo test") == "Echo test"
    assert serial_wrapper.serial.is_open
    assert caplog.record_tuples == [
        ('sbot.internal.serial_wrapper', logging.INFO, 'Connected to board Test board:5678'),
        ('sbot.internal.serial_wrapper', 5, "Serial write - 'Echo test'"),
        ('sbot.internal.serial_wrapper', 5, "Serial read  - 'Echo test'"),
    ]

    # Test that an exception is raised if a NACK is received
    with pytest.raises(RuntimeError, match="Test exception"):
        serial_wrapper.write("NACK:Test exception")


def test_serial_wrapper_invalid_port() -> None:
    """
    Test that a BoardDisconnectionError is raised when the serial port is cannot be opened.
    """
    serial_wrapper = SerialWrapper(
        port='socket://localhost:1',  # A port that has nothing listening on it
        baud=115200,
    )
    with pytest.raises(
        BoardDisconnectionError,
        match="Connection to board : could not be established"
    ):
        serial_wrapper.query("Echo test")


def test_serial_wrapper_message_timeout(caplog, monkeypatch) -> None:
    """
    Test that a BoardDisconnectionError is raised when the serial response times out.
    """
    # Capture all logging
    caplog.set_level(0)
    serial_wrapper = SerialWrapper(
        port='loop://',
        baud=115200,
    )

    # Allow the serial port to be opened
    assert serial_wrapper.query("Echo test") == "Echo test"
    caplog.clear()

    monkeypatch.setattr(serial_wrapper.serial, 'readline', lambda: b'')
    with pytest.raises(
        BoardDisconnectionError,
        match="Board : disconnected during transaction"
    ):
        serial_wrapper.query("Echo test")

    assert caplog.record_tuples == [
        ('sbot.internal.serial_wrapper', 5, "Serial write - 'Echo test'"),
        ('sbot.internal.serial_wrapper', 5, "Serial read  - ''"),
        ('sbot.internal.serial_wrapper', logging.WARNING,
         'Connection to board : timed out waiting for response'),
        ('sbot.internal.serial_wrapper', logging.WARNING, 'Board : disconnected'),

        ('sbot.internal.serial_wrapper', logging.INFO, 'Connected to board :'),
        ('sbot.internal.serial_wrapper', 5, "Serial write - 'Echo test'"),
        ('sbot.internal.serial_wrapper', 5, "Serial read  - ''"),
        ('sbot.internal.serial_wrapper', logging.WARNING,
         'Connection to board : timed out waiting for response'),
        ('sbot.internal.serial_wrapper', logging.WARNING, 'Board : disconnected'),

        ('sbot.internal.serial_wrapper', logging.INFO, 'Connected to board :'),
        ('sbot.internal.serial_wrapper', 5, "Serial write - 'Echo test'"),
        ('sbot.internal.serial_wrapper', 5, "Serial read  - ''"),
        ('sbot.internal.serial_wrapper', logging.WARNING,
         'Connection to board : timed out waiting for response'),
        ('sbot.internal.serial_wrapper', logging.WARNING, 'Board : disconnected'),

        ('sbot.internal.serial_wrapper', logging.INFO, 'Connected to board :'),
        ('sbot.internal.serial_wrapper', 5, "Serial write - 'Echo test'"),
        ('sbot.internal.serial_wrapper', 5, "Serial read  - ''"),
        ('sbot.internal.serial_wrapper', logging.WARNING,
         'Connection to board : timed out waiting for response'),
        ('sbot.internal.serial_wrapper', logging.WARNING, 'Board : disconnected'),
    ]

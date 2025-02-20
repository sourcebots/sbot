"""Exceptions used by the sbot package."""


class MetadataKeyError(KeyError):
    """
    Raised when trying to access a metadata key for which no value exists.

    :param key: The key that was not found
    """

    def __init__(self, key: str):
        self.key = key

    def __str__(self) -> str:
        return f"Key {self.key!r} not present in metadata"


class MetadataNotReadyError(RuntimeError):
    """Raised when trying to access metadata before wait_start has been called."""

    def __str__(self) -> str:
        return (
            "Metadata (e.g. zone or is_competition) can only be used after"
            " wait_start has been called"
        )


class BoardDisconnectionError(IOError):
    """Raised when communication to a board fails and cannot be reestablished."""

    pass


class IncorrectBoardError(IOError):
    """
    Raised when a board returns the wrong board type in response to *IDN?.

    This is usually caused by a board being provided the wrong serial port.

    :param board_type: The board type returned by the board
    :param expected_type: The board type expected by the class
    """

    def __init__(self, board_type: str, expected_type: str):
        self.returned_type = board_type
        self.expected_type = expected_type

    def __str__(self) -> str:
        return f"Board returned type {self.returned_type!r}, expected {self.expected_type!r}"

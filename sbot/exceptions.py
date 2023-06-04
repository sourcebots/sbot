class MetadataKeyError(KeyError):
    """Raised when trying to access a metadata key for which no value exists."""

    def __init__(self, key: str):
        self.key = key

    def __str__(self) -> str:
        return f"Key {self.key!r} not present in metadata, or no metadata was available"


class MetadataNotReadyError(RuntimeError):
    """Raised when trying to access metadata before it has been loaded."""

    def __str__(self) -> str:
        return (
            "Metadata (e.g. zone or is_competition) can only be used after"
            " wait_start has been called"
        )
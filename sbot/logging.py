"""Logger Setup."""
import logging
import sys


def logger_setup() -> None:
    """Setup the logger."""
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)

    formatter = logging.Formatter('%(name)s - %(message)s')
    handler.setFormatter(formatter)

    root.addHandler(handler)

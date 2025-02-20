"""Module for loading the overrides from the .env file and environment variables."""
from __future__ import annotations

import os

from dotenv import dotenv_values

_OVERRIDES: dict[str, str | None] = {}


def load_overrides() -> None:
    """Load the overrides from the .env file and environment variables."""
    # Load the .env file
    config = dotenv_values("override.env")

    # Make config keys uppercase
    config = {key.upper(): value for key, value in config.items()}

    # Load from environment variables prefixed with SBOT_
    config_from_env = {
        name.replace("SBOT_", "", 1): value
        for name, value in os.environ.items()
        if name.startswith("SBOT_")
    }

    # Update the overrides, with the config file taking precedence
    _OVERRIDES.update(config_from_env)
    _OVERRIDES.update(config)


def get_overrides() -> dict[str, str | None]:
    """Get a reference to the global overrides dictionary."""
    return _OVERRIDES


# Load the overrides when this module is imported
load_overrides()

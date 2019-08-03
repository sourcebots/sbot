"""
Implementation of loading metadata.

Metadata is a dictionary of arbitrary information about the environment that the robot is
running in. It usually includes the starting zone and a flag indicating whether we are in
competition or development mode. Metadata is stored in a JSON file, typically on a
competition USB stick. The environment variable SBOT_METADATA_PATH specifies a directory
that is (recursively) searched for a JSON file to load.

Example metadata file:

    {
        "arena": "A",
        "zone": 2,
        "is_competition": true
    }
"""

import json
import logging
import os
from typing import Any, Dict, Optional

LOGGER = logging.getLogger(__name__)

METADATA_ENV_VAR = "SBOT_METADATA_PATH"


class MetadataKeyError(KeyError):
    """Raised when trying to access a metadata key for which no value exists."""

    def __init__(self, key: str):
        self.key = key

    def __str__(self) -> str:
        return f"Key {self.key!r} not present in metadata, or no metadata was available"


def load(*, fallback: Dict[str, Any] = {}) -> Dict[str, Any]:
    """
    Searches the path identified by METADATA_ENV_VAR for a JSON file and reads it.

    If no file is found, it falls back to the `fallback` dict.
    """
    search_path = os.environ.get(METADATA_ENV_VAR)
    if search_path:
        path = _find_file(search_path)
        if path:
            LOGGER.info(f"Loading metadata from {path}")
            return _read_file(path)
        else:
            LOGGER.info(f"No JSON metadata files found in {search_path}")
    else:
        LOGGER.info(f"{METADATA_ENV_VAR} not set, not loading metadata")
    return fallback


def _find_file(search_path: str) -> Optional[str]:
    for dir_path, dir_names, file_names in os.walk(search_path):
        for file_name in file_names:
            if file_name.endswith(".json"):
                return os.path.join(dir_path, file_name)
    return None


def _read_file(path: str) -> Dict[str, Any]:
    with open(path) as file:
        try:
            obj = json.load(file)
        except json.decoder.JSONDecodeError:
            raise RuntimeError("Unable to decode metadata. Ask a volunteer for help.")
    if isinstance(obj, dict):
        return obj
    else:
        raise TypeError("Top-level value in metadata file must be a JSON object")

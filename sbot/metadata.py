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
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import TypedDict

from .exceptions import MetadataKeyError

logger = logging.getLogger(__name__)

METADATA_ENV_VAR = "SBOT_METADATA_PATH"
METADATA_NAME = "metadata.json"


class Metadata(TypedDict):
    is_competition: bool
    zone: int


DEFAULT_METADATA: Metadata = {
    "is_competition": False,
    "zone": 0,
}


def load() -> Metadata:
    """
    Searches the path identified by METADATA_ENV_VAR for a JSON file and reads it.

    If no file is found, it falls back to the default dict.
    """
    search_path = os.environ.get(METADATA_ENV_VAR)
    if search_path:
        for item in Path(search_path).iterdir():
            if item.is_dir():
                if (item / METADATA_NAME).exists():
                    return _load_metadata(item / METADATA_NAME)
            else:
                if item.name == METADATA_NAME:
                    return _load_metadata(item / METADATA_NAME)
        else:
            logger.info(f"No JSON metadata files found in {search_path}")
    else:
        logger.info(f"{METADATA_ENV_VAR} not set, not loading metadata")
    return DEFAULT_METADATA


def _load_metadata(path: Path) -> Metadata:
    logger.info(f"Loading metadata from {path}")
    with path.open() as file:
        try:
            obj: Metadata = json.load(file)
        except json.decoder.JSONDecodeError as e:
            raise RuntimeError("Unable to load metadata.") from e

    if not isinstance(obj, dict):
        raise TypeError(f"Found metadata file, but format is invalid. Got: {obj}")

    # check required keys exist at runtime
    for key in Metadata.__annotations__.keys():
        if key not in obj.keys():
            raise MetadataKeyError(key)

    return obj

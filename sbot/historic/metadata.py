"""
Implementation of loading metadata.

Metadata is a dictionary of information about the environment that the robot is running in.
It usually includes the starting zone and a flag indicating whether we are in
competition or development mode. Metadata is stored in a JSON file, typically on a
competition USB stick. The environment variable SBOT_METADATA_PATH specifies a directory
where it, and its children, are searched for the JSON file to load.

Example metadata file:
```json
{
    "zone": 2,
    "is_competition": true
}
```
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import TypedDict

from ..internal.exceptions import MetadataKeyError

logger = logging.getLogger(__name__)

# The name of the environment variable that specifies the path to search
# for metadata USB sticks
METADATA_ENV_VAR = "SBOT_METADATA_PATH"
# The name of the metadata file
METADATA_NAME = "metadata.json"


class Metadata(TypedDict):
    """
    The structure of the metadata dictionary.

    :param is_competition: Whether the robot is in competition mode
    :param zone: The zone that the robot is in
    """

    is_competition: bool
    zone: int


# The default metadata to use if no file is found
DEFAULT_METADATA: Metadata = {
    "is_competition": False,
    "zone": 0,
}


def load() -> Metadata:
    """
    Search for a metadata file and load it.

    Searches the path identified by SBOT_METADATA_PATH and its children for
    metadata.json (set by METADATA_NAME) and reads it.

    :raises FileNotFoundError: If no metadata file is found
    :return: The metadata dictionary, either loaded from a file or the default
    """
    search_path = os.environ.get(METADATA_ENV_VAR)
    if search_path:
        search_root = Path(search_path)
        if not search_root.is_dir():
            raise FileNotFoundError(f"Metaddata path {search_path} does not exist")
        for item in Path(search_path).iterdir():
            try:
                if item.is_dir() and (item / METADATA_NAME).exists():
                    return _load_metadata(item / METADATA_NAME)
                elif item.name == METADATA_NAME:
                    return _load_metadata(item)
            except PermissionError:
                logger.debug(f"Unable to read {item}")
        else:
            logger.info(f"No JSON metadata files found in {search_path}")
    else:
        logger.info(f"{METADATA_ENV_VAR} not set, not loading metadata")
    return DEFAULT_METADATA


def _load_metadata(path: Path) -> Metadata:
    """
    Load the metadata from a JSON file, found by `load`.

    The file must be a JSON dictionary with the keys `is_competition` and `zone`.

    :param path: The path to the metadata file
    :raises RuntimeError: If the metadata file is invalid JSON
    :raises TypeError: If the metadata file is not a JSON dictionary
    :raises MetadataKeyError: If the metadata file is missing a required key
    :return: The metadata dictionary
    """
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

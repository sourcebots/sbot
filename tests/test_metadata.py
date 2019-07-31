"""Test Metadata Loading."""

from os import environ
from pathlib import Path

from pytest import raises

from sbot.metadata import METADATA_ENV_VAR, MetadataKeyError, load


def test_metadata_env_var() -> None:
    """Check that the env_var is as expected."""
    assert METADATA_ENV_VAR == "SBOT_METADATA_PATH"


def test_metadata_key_error() -> None:
    """Test the key error exception."""
    e = MetadataKeyError("beans")

    assert str(e) == "Key \'beans\' not present in metadata, or no metadata was available"


def test_load_no_env_var() -> None:
    """Test the behaviour when the environment variable is not set."""
    data = load()
    assert data == {}
    data = load(fallback={"beans": 5})
    assert data == {"beans": 5}


def test_load_file() -> None:
    """Test that we can load a file."""
    data_path = Path(__file__).parent
    environ[METADATA_ENV_VAR] = str(data_path.absolute())

    data = load()
    assert data == {"is_competition": True, "zone": 1}

    data = load(fallback={"beans": 5})
    assert data == {"is_competition": True, "zone": 1}


def test_load_file_not_found() -> None:
    """Test that the fallback data is loaded if no file is found."""
    data_path = Path(__file__).parent.joinpath("test_data", "empty")
    environ[METADATA_ENV_VAR] = str(data_path.absolute())

    data = load()
    assert data == {}

    data = load(fallback={"beans": 5})
    assert data == {"beans": 5}


def test_load_bad_file() -> None:
    """Test that an exception is thrown when the JSON file is bad."""
    data_path = Path(__file__).parent.joinpath("test_data", "bad")
    environ[METADATA_ENV_VAR] = str(data_path.absolute())

    load()


def test_load_bad_data() -> None:
    """Test that an exception is thrown when the JSON is not an object."""
    data_path = Path(__file__).parent.joinpath("test_data", "not_object")
    environ[METADATA_ENV_VAR] = str(data_path.absolute())

    with raises(TypeError):
        load()

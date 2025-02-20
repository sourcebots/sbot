"""Test Metadata Loading."""

from pathlib import Path

from pytest import raises

from sbot._comp import METADATA_ENV_VAR, Comp, MetadataKeyError, Metadata


def load() -> Metadata:
    """Load the metadata."""
    comp = Comp()
    comp._load()
    return comp._metadata


def test_metadata_env_var() -> None:
    """Check that the env_var is as expected."""
    assert METADATA_ENV_VAR == "SBOT_METADATA_PATH"


def test_metadata_key_error() -> None:
    """Test the key error exception."""
    e = MetadataKeyError("beans")

    assert str(e) == "Key \'beans\' not present in metadata"


def test_load_no_env_var(monkeypatch) -> None:
    """Test the behaviour when the environment variable is not set."""
    monkeypatch.delenv(METADATA_ENV_VAR, raising=False)
    data = load()
    assert data == {"is_competition": False, "zone": 0}


def test_load_file(monkeypatch) -> None:
    """Test that we can load a file."""
    data_path = Path(__file__).parent / 'test_data/valid'
    monkeypatch.setenv(METADATA_ENV_VAR, str(data_path.absolute()))

    data = load()
    assert data == {"is_competition": True, "zone": 1}


def test_load_nested_file(monkeypatch) -> None:
    """Test that we can load a file from a nested directory."""
    data_path = Path(__file__).parent / 'test_data/nested'
    monkeypatch.setenv(METADATA_ENV_VAR, str(data_path.absolute()))

    data = load()
    assert data == {"is_competition": True, "zone": 1}


def test_load_file_not_found(monkeypatch) -> None:
    """Test that the fallback data is loaded if no file is found."""
    data_path = Path(__file__).parent / "test_data/empty"
    monkeypatch.setenv(METADATA_ENV_VAR, str(data_path.absolute()))

    data = load()
    assert data == {"is_competition": False, "zone": 0}


def test_load_bad_file(monkeypatch) -> None:
    """Test that an exception is thrown when the JSON file is bad."""
    data_path = Path(__file__).parent / "test_data/bad"
    monkeypatch.setenv(METADATA_ENV_VAR, str(data_path.absolute()))

    with raises(RuntimeError):
        load()


def test_load_bad_data(monkeypatch) -> None:
    """Test that an exception is thrown when the JSON is not an object."""
    data_path = Path(__file__).parent / "test_data/not_object"
    monkeypatch.setenv(METADATA_ENV_VAR, str(data_path.absolute()))

    with raises(TypeError):
        load()


def test_load_bad_key(monkeypatch) -> None:
    """Test that an exception is thrown when the JSON has a missing key."""
    data_path = Path(__file__).parent / "test_data/missing_key"
    monkeypatch.setenv(METADATA_ENV_VAR, str(data_path.absolute()))

    with raises(MetadataKeyError):
        load()


def test_missing_metadata_path(monkeypatch) -> None:
    """Test that an exception is thrown when the metadata path does not exist."""
    data_path = Path(__file__).parent / "test_data/missing_path"
    monkeypatch.setenv(METADATA_ENV_VAR, str(data_path.absolute()))

    with raises(FileNotFoundError):
        load()

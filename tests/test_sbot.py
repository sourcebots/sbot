"""Test that the module works."""
from sbot import __version__


def test_import() -> None:
    """Test that we can import the module."""
    import sbot  # noqa: F401


def test_version() -> None:
    """Test that the version is as expected."""
    assert __version__ == '0.2.0'

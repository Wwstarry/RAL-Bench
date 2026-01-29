"""Tests for main module."""

import pytest
from thefuck.main import main


def test_main_no_args():
    """Test main with no arguments."""
    result = main([])
    assert result == 1


def test_main_version():
    """Test main with --version flag."""
    with pytest.raises(SystemExit) as exc_info:
        main(["--version"])
    assert exc_info.value.code == 0
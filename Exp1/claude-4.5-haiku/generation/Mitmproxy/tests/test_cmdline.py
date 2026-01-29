"""
Test command line argument parsing.
"""

import pytest
from mitmproxy.tools.cmdline import mitmdump


def test_mitmdump_parser_creation():
    """Test that mitmdump parser can be created."""
    parser = mitmdump()
    assert parser is not None


def test_mitmdump_parser_default_args():
    """Test parsing default arguments."""
    parser = mitmdump()
    args = parser.parse_args([])
    assert args.listen_host == "127.0.0.1"
    assert args.listen_port == 8080
    assert args.mode == "regular"
    assert args.verbose is False
    assert args.quiet is False


def test_mitmdump_parser_custom_host():
    """Test parsing custom host."""
    parser = mitmdump()
    args = parser.parse_args(["-l", "0.0.0.0"])
    assert args.listen_host == "0.0.0.0"


def test_mitmdump_parser_custom_port():
    """Test parsing custom port."""
    parser = mitmdump()
    args = parser.parse_args(["-p", "9090"])
    assert args.listen_port == 9090


def test_mitmdump_parser_mode():
    """Test parsing mode argument."""
    parser = mitmdump()
    args = parser.parse_args(["-m", "transparent"])
    assert args.mode == "transparent"


def test_mitmdump_parser_verbose():
    """Test parsing verbose flag."""
    parser = mitmdump()
    args = parser.parse_args(["-v"])
    assert args.verbose is True


def test_mitmdump_parser_quiet():
    """Test parsing quiet flag."""
    parser = mitmdump()
    args = parser.parse_args(["-q"])
    assert args.quiet is True


def test_mitmdump_parser_flow_detail():
    """Test parsing flow detail level."""
    parser = mitmdump()
    args = parser.parse_args(["-d", "3"])
    assert args.flow_detail == 3


def test_mitmdump_parser_script():
    """Test parsing script argument."""
    parser = mitmdump()
    args = parser.parse_args(["-s", "addon.py"])
    assert args.scripts == ["addon.py"]


def test_mitmdump_parser_multiple_scripts():
    """Test parsing multiple script arguments."""
    parser = mitmdump()
    args = parser.parse_args(["-s", "addon1.py", "-s", "addon2.py"])
    assert args.scripts == ["addon1.py", "addon2.py"]
"""Tests for Command class."""

import pytest
from thefuck.command import Command


def test_command_creation():
    """Test creating a Command object."""
    cmd = Command("ls -la", stdout="file1\nfile2", stderr="", returncode=0)
    assert cmd.script == "ls -la"
    assert cmd.stdout == "file1\nfile2"
    assert cmd.stderr == ""
    assert cmd.returncode == 0


def test_command_output():
    """Test Command.output property."""
    cmd = Command("ls", stdout="file1", stderr="error", returncode=1)
    assert cmd.output == "file1error"


def test_command_str():
    """Test Command string representation."""
    cmd = Command("echo hello")
    assert str(cmd) == "echo hello"
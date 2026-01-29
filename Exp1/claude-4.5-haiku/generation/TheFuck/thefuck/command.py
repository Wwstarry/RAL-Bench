"""Command representation and utilities."""

import os
from typing import Optional


class Command:
    """Represents a shell command with its output and return code."""
    
    def __init__(
        self,
        script: str,
        stdout: str = "",
        stderr: str = "",
        returncode: int = 0
    ):
        """Initialize a Command.
        
        Args:
            script: The command line that was executed
            stdout: Standard output from the command
            stderr: Standard error from the command
            returncode: Return code from the command
        """
        self.script = script
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode
    
    def __str__(self):
        return self.script
    
    def __repr__(self):
        return f"Command({self.script!r}, stdout={self.stdout!r}, stderr={self.stderr!r}, returncode={self.returncode})"
    
    @property
    def output(self):
        """Combined stdout and stderr."""
        return self.stdout + self.stderr
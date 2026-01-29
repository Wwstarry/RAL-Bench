"""
Data types for TheFuck.
"""

from typing import List, Optional, Dict, Any, Tuple
import os
import subprocess


class Command:
    """Represents a previously executed command."""

    def __init__(
        self,
        script: str,
        stdout: str = "",
        stderr: str = "",
        return_code: int = 0
    ):
        self.script = script
        self.stdout = stdout
        self.stderr = stderr
        self.return_code = return_code

    def __eq__(self, other):
        if not isinstance(other, Command):
            return False
        return (self.script == other.script and
                self.stdout == other.stdout and
                self.stderr == other.stderr and
                self.return_code == other.return_code)


def get_all_executables() -> List[str]:
    """Returns all executable names in PATH."""
    executables = []
    for path in os.environ.get("PATH", "").split(os.pathsep):
        if os.path.isdir(path):
            executables.extend(
                cmd for cmd in os.listdir(path)
                if os.path.isfile(os.path.join(path, cmd)) and
                os.access(os.path.join(path, cmd), os.X_OK)
            )
    return sorted(set(executables))


def get_command_output(command: str) -> Tuple[str, str, int]:
    """Executes a command and returns stdout, stderr, and return code."""
    try:
        process = subprocess.run(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        return process.stdout, process.stderr, process.returncode
    except Exception:
        return "", "Command execution failed", 1


def get_shell_history() -> List[str]:
    """Returns a list of recent commands from shell history."""
    history_file = os.path.expanduser("~/.bash_history")
    if not os.path.exists(history_file):
        return []
    
    try:
        with open(history_file, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    except Exception:
        return []
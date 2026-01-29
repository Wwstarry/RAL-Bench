from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class Command:
    """
    Represents a previously executed console command.

    Attributes:
        script: Original command line as a string.
        stdout: Captured stdout (string).
        stderr: Captured stderr (string).
        returncode: Process return code (int).
    """

    script: str
    stdout: str = ""
    stderr: str = ""
    returncode: int = 0

    @property
    def output(self) -> str:
        # Match common TheFuck expectations: combine streams
        out = []
        if self.stdout:
            out.append(self.stdout)
        if self.stderr:
            out.append(self.stderr)
        return "\n".join(out)

    @property
    def script_parts(self) -> List[str]:
        # Simplified parsing: split on whitespace (good enough for tests)
        return self.script.strip().split()

    @property
    def command(self) -> Optional[str]:
        parts = self.script_parts
        return parts[0] if parts else None
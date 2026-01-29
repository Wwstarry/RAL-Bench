from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional


@dataclass(frozen=True)
class Command:
    """
    Captures the previous command and its result.

    - script: full command line as typed (string)
    - stdout/stderr: captured outputs
    - returncode: integer return code (0 means success)
    """

    script: str
    stdout: str = ""
    stderr: str = ""
    returncode: int = 0

    @property
    def output(self) -> str:
        # Match typical "thefuck" behavior: combine stderr and stdout.
        out = ""
        if self.stderr:
            out += self.stderr
        if self.stdout:
            if out:
                out += "\n"
            out += self.stdout
        return out

    @property
    def script_parts(self) -> List[str]:
        # Simple shell-like split sufficient for tests (no complex quoting).
        return [p for p in self.script.strip().split() if p]

    @property
    def command(self) -> Optional[str]:
        parts = self.script_parts
        return parts[0] if parts else None

    @property
    def args(self) -> List[str]:
        parts = self.script_parts
        return parts[1:] if len(parts) > 1 else []

    def __iter__(self) -> Iterable[str]:
        return iter(self.script_parts)
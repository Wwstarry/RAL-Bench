from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional
import shlex


@dataclass(frozen=True)
class Command:
    """
    Represents a previously executed console command.
    """
    script: str
    stdout: str = ""
    stderr: str = ""
    return_code: int = 0

    @property
    def output(self) -> str:
        out = self.stdout or ""
        err = self.stderr or ""
        if out and err:
            return out + "\n" + err
        return out or err

    @property
    def tokens(self) -> List[str]:
        try:
            return shlex.split(self.script)
        except Exception:
            # Fallback naive split
            return self.script.split()

    def with_script(self, new_script: str) -> "Command":
        return Command(script=new_script, stdout=self.stdout, stderr=self.stderr, return_code=self.return_code)


@dataclass(order=True, frozen=True)
class Suggestion:
    """
    A suggested corrected command.
    """
    sort_index: float = field(init=False, repr=False)
    script: str
    priority: int = 0
    rule: str = ""

    def __post_init__(self):
        # Higher priority should be first, but dataclass ordering sorts ascending,
        # so use negative priority as sort_index
        object.__setattr__(self, "sort_index", -float(self.priority))
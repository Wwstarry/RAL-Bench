from __future__ import annotations

from dataclasses import dataclass, field

from .utils import shell_split


@dataclass(frozen=True)
class Command:
    """
    Representation of a previously executed command.
    """

    script: str
    stdout: str = ""
    stderr: str = ""
    returncode: int = 0
    args: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.args:
            object.__setattr__(self, "args", shell_split(self.script or ""))

    @classmethod
    def from_raw(
        cls, script: str, stdout: str = "", stderr: str = "", returncode: int = 0
    ) -> "Command":
        return cls(script=script, stdout=stdout, stderr=stderr, returncode=returncode)
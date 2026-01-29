"""
Very small re-implementation of the *Command* helper from *The Fuck*.

It is nothing more than a glorified named-tuple but with a few convenience
methods that the rules can rely on.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(slots=True)
class Command:
    """
    A representation of a (failed) shell command.

    Parameters
    ----------
    script:
        The command line that was executed (string as typed in the shell).
    stdout:
        Standard output captured from the failed command.
    stderr:
        Standard error captured from the failed command.
    exit_code:
        Exit status returned by the process.
    """

    script: str
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 1

    @property
    def parts(self) -> list[str]:
        """
        Returns a (very naive) shlex split of :pyattr:`script`.

        The real *The Fuck* is a lot more sophisticated – for the subset required
        by the kata it is enough to just ``.split()``.  This is *good enough* for
        the covered scenarios and avoids a heavy dependency on ``shlex`` which
        deals with quoting/escaping, etc.
        """
        return self.script.split()

    def __repr__(self) -> str:      # pragma: no cover
        return (
            "Command("
            f"script={self.script!r}, "
            f"stdout={self.stdout!r}, "
            f"stderr={self.stderr!r}, "
            f"exit_code={self.exit_code}"
            ")"
        )
from __future__ import annotations

import io
import re


class StdSim(io.StringIO):
    """A simple stdout/stderr simulator for capturing output during tests."""

    def __init__(self, initial_value: str = "", newline: str | None = None) -> None:
        super().__init__(initial_value, newline=newline)
        self._encoding = "utf-8"

    @property
    def encoding(self) -> str:
        return self._encoding

    def isatty(self) -> bool:
        return False


_ANSI_RE = re.compile(
    r"""
    \x1B  # ESC
    (?:
        \[ [0-?]* [ -/]* [@-~]     # CSI ... Cmd
        |
        \] .*? (?:\x07|\x1B\\)     # OSC ... BEL or ST
        |
        [PX^_] .*? \x1B\\          # DCS/SOS/PM/APC ... ST
        |
        [()#][0-9A-Za-z]           # charset / other single escape
        |
        [A-Za-z]                   # single-character command
    )
    """,
    re.VERBOSE | re.DOTALL,
)


def strip_ansi(text: str) -> str:
    """Remove common ANSI escape sequences from text."""
    return _ANSI_RE.sub("", text)


def normalize_newlines(text: str) -> str:
    """Normalize CRLF/CR to LF."""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def remove_trailing_whitespace(text: str) -> str:
    """Remove trailing whitespace from each line (preserving line structure)."""
    text = normalize_newlines(text)
    lines = text.split("\n")
    lines = [ln.rstrip() for ln in lines]
    return "\n".join(lines)
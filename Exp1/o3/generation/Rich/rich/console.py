"""
Very small re-implementation of `rich.console.Console`.
Only features that are required by the automated tests have been implemented.
"""

from __future__ import annotations

import io
import os
import sys
import textwrap
import re
from typing import Any, Iterable

# --------------------------------------------------------------------------- #
# helper                                                                     #
# --------------------------------------------------------------------------- #


_EMOJI_MAP = {
    "rocket": "🚀",
    "smiley": "😃",
    "thumbs_up": "👍",
    "snake": "🐍",
    "robot": "🤖",
    # add more here if new tests require them
}

_MARKUP_RE = re.compile(r"\[/?[^\]]+\]")


def _strip_markup(text: str) -> str:
    """
    Remove very simple Rich markup tags such as ``[bold]hello[/bold]``.
    This does **not** try to validate or correctly nest tags – it just
    deletes anything that looks like ``[tag]`` or ``[/tag]``.
    """
    return _MARKUP_RE.sub("", text)


def _replace_emoji(text: str) -> str:
    """
    Replace :emoji: codes with actual unicode characters using the limited
    ``_EMOJI_MAP`` defined above.
    """
    def repl(match: re.Match[str]) -> str:
        name = match.group(1)
        return _EMOJI_MAP.get(name, match.group(0))  # keep untouched if unknown

    return re.sub(r":([a-z0-9_]+):", repl, text, flags=re.IGNORECASE)


def _stringify(obj: Any) -> str:
    """
    Convert the given object to a string in a Rich-compatible way.  Classes
    like *Table* and *Progress* implement ``__str__`` so this just forwards
    to that.  Real Rich uses more sophisticated logic but that isn’t required
    here.
    """
    if isinstance(obj, str):
        return obj
    if hasattr(obj, "__rich__"):
        # allow user objects to supply their own renderable
        try:
            return str(obj.__rich__())
        except Exception:  # pragma: no cover
            # fall-through to plain str if their implementation misbehaves
            pass
    return str(obj)


# --------------------------------------------------------------------------- #
# Console                                                                     #
# --------------------------------------------------------------------------- #


class Console:
    """
    A *much* simplified re-implementation of :class:`rich.console.Console`.

    Only a subset of keyword arguments are accepted and most optional
    methods of the original class are *not* present.  Enough functionality
    is included for pretty printing, simple markup handling, emoji
    replacement and text wrapping.
    """

    def __init__(
        self,
        *,
        width: int | None = None,
        file: io.TextIOBase | None = None,
        record: bool = False,
    ) -> None:
        self.width: int | None = width or int(os.environ.get("COLUMNS", 80))
        self.file: io.TextIOBase = file or sys.stdout
        self._record: bool = record
        self._record_buffer: list[str] = []

    # --------------------------------------------------------------------- #
    # public API                                                            #
    # --------------------------------------------------------------------- #

    def print(  # noqa: D401  (Rich’s own API uses *print*)
        self,
        *objects: Any,
        sep: str = " ",
        end: str = "\n",
        markup: bool = True,
        emoji: bool = True,
        wrap: bool = True,
    ) -> None:
        """
        Rich-style print replacement.

        Parameters
        ----------
        objects:
            Objects or strings to print.
        markup:
            Whether to interpret ``[style]`` markup.
        emoji:
            Whether to convert ``:emoji:`` short-codes.
        wrap:
            Apply word-wrapping to long text that exceeds *width*.
        """

        # 1. stringify
        pieces: list[str] = [_stringify(obj) for obj in objects]
        combined: str = sep.join(pieces)

        # 2. markup + emoji
        if markup:
            combined = _strip_markup(combined)
        if emoji:
            combined = _replace_emoji(combined)

        # 3. wrapping
        if wrap and self.width:
            combined = "\n".join(
                textwrap.fill(line, self.width, replace_whitespace=False)
                for line in combined.splitlines()
            )

        # 4. write
        self.file.write(combined + end)
        self.file.flush()

        # 5. record
        if self._record:
            self._record_buffer.append(combined + end)

    # alias used by some libraries/tests
    def log(self, *objects: Any, **kwargs: Any) -> None:  # pragma: no cover
        """`Console.log` is mapped to `Console.print` in this tiny variant."""
        self.print(*objects, **kwargs)

    # recording helpers (subset)
    def export_text(self) -> str:
        """
        Return everything that has been printed since the console was created
        *if* the *record* flag was set to *True*.
        """
        return "".join(self._record_buffer)
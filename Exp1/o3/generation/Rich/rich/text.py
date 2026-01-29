"""
A minimal re-implementation of *rich.text.Text*.
"""

from __future__ import annotations

import re
from typing import Any

from .console import _strip_markup, _replace_emoji


class Text:
    """
    Tiny stub of :class:`rich.text.Text`.

    The object basically behaves like an immutable unicode string while keeping
    *style* information around for compatibility.  Only the behaviour needed by
    the unit tests is implemented.
    """

    def __init__(self, text: str = "", style: str | None = None) -> None:
        self._text: str = str(text)
        self.style: str | None = style

    # factory helpers ----------------------------------------------------- #

    @classmethod
    def from_markup(cls, markup_text: str, *, style: str | None = None) -> "Text":
        cleaned = _strip_markup(markup_text)
        cleaned = _replace_emoji(cleaned)
        return cls(cleaned, style=style)

    # dunder emulation – allow `str(Text(...))` / concatenation ----------- #

    def __str__(self) -> str:  # noqa: Dunder
        return self._text

    def __repr__(self) -> str:  # pragma: no cover
        return f"Text({self._text!r}, style={self.style!r})"

    # basic concatenation to behave like the original object
    def __add__(self, other: Any) -> "Text":  # noqa: Dunder
        return Text(self._text + str(other), style=self.style)

    __radd__ = __add__

    # equality for tests
    def __eq__(self, other: object) -> bool:  # noqa: Dunder
        if isinstance(other, Text):
            return self._text == other._text
        return self._text == str(other)

    # expose plain text
    def plain(self) -> str:  # noqa: D401
        return self._text


__all__ = ["Text"]
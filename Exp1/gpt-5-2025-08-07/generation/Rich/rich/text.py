from __future__ import annotations

import re
from typing import Iterable, Optional, Union

from .console import _replace_emoji, _strip_markup


class Text:
    """
    Minimal Text object compatible with Rich's Text for simple use-cases.
    It primarily stores plain text and ignores advanced styling.
    """

    def __init__(self, text: str = "", style: Optional[str] = None, no_wrap: bool = False) -> None:
        self.plain: str = text
        self.style = style
        self.no_wrap = no_wrap

    def __str__(self) -> str:
        return self.plain

    def __repr__(self) -> str:
        return f"Text({self.plain!r}, style={self.style!r})"

    def __add__(self, other: Union[str, "Text"]) -> "Text":
        if isinstance(other, Text):
            return Text(self.plain + other.plain)
        return Text(self.plain + str(other))

    def append(self, text: Union[str, "Text"]) -> None:
        if isinstance(text, Text):
            self.plain += text.plain
        else:
            self.plain += str(text)

    @classmethod
    def from_markup(cls, text: str, emoji: bool = True) -> "Text":
        t = _strip_markup(text)
        if emoji:
            t = _replace_emoji(t)
        return cls(t)

    def expand_tabs(self, tabsize: int = 8) -> "Text":
        self.plain = self.plain.expandtabs(tabsize)
        return self

    def wrap(self, width: int) -> list["Text"]:
        if width <= 0 or self.no_wrap:
            return [Text(self.plain)]
        lines = []
        line = ""
        for ch in self.plain:
            if ch == "\n":
                lines.append(Text(line))
                line = ""
                continue
            if len(line) >= width:
                lines.append(Text(line))
                line = ch
            else:
                line += ch
        lines.append(Text(line))
        return lines
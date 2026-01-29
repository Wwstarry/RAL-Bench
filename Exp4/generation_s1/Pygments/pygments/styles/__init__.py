"""Minimal style system compatible with a small subset of Pygments.

Avoid circular imports: Style base is defined here; concrete styles live in
separate modules and may import Style from here.
"""

from __future__ import annotations

from typing import Dict, Optional

from pygments.token import Token, TokenType
from pygments.util import ClassNotFound


class Style:
    """
    Base class for styles.

    Subclasses should override:
      - styles: dict mapping TokenType -> style string
      - background_color, highlight_color, default_style (optional)
    """

    background_color: Optional[str] = None
    highlight_color: Optional[str] = None
    default_style: str = ""

    # mapping TokenType -> "style string"
    styles: Dict[TokenType, str] = {}

    @classmethod
    def style_for_token(cls, ttype: TokenType) -> str:
        """Return the style string for the token type, walking up parents."""
        cur = ttype
        while cur is not None and cur is not Token:
            if cur in cls.styles:
                return cls.styles[cur]
            cur = getattr(cur, "parent", None)
        # allow exact Token mapping too
        if Token in cls.styles:
            return cls.styles[Token]
        return cls.default_style or ""


def get_style_by_name(name: str):
    nm = (name or "default").lower()
    if nm in ("default", "friendly"):
        # Import lazily to avoid circular import at module import time.
        from .default import DefaultStyle

        return DefaultStyle
    raise ClassNotFound(f"no style found for {name!r}")


__all__ = ["Style", "get_style_by_name"]
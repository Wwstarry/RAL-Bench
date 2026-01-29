"""
Extremely small placeholder for *rich.theme.Theme*.

Real styling is not needed for the tests – the class is only required for
import-time compatibility.
"""

from __future__ import annotations


class Theme:
    def __init__(self, styles=None) -> None:  # noqa: D401
        self.styles = dict(styles or {})

    def __repr__(self) -> str:  # pragma: no cover
        return f"Theme({self.styles})"


__all__ = ["Theme"]
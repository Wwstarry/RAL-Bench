"""
Very small subset of the Pygments style system.
"""

from typing import Dict, Type

from pygments.token import Token

__all__ = ["Style", "DefaultStyle", "get_style_by_name"]

###############################################################################
# Base Style
###############################################################################


class Style:
    """
    Minimal style: subclasses must define ``styles`` dict mapping Token to css
    style strings.
    """

    styles: Dict[Token, str] = {}


###############################################################################
# Default style
###############################################################################


class DefaultStyle(Style):
    styles = {
        Token: "",  # catch-all
        Token.Comment: "italic #888",
        Token.Keyword: "bold #005",
        Token.Name: "#333",
        Token.Name.Function: "bold #900",
        Token.String: "#070",
        Token.Number: "#099",
        Token.Operator: "#000",
        Token.Punctuation: "#000",
    }


_STYLES: Dict[str, Type[Style]] = {
    "default": DefaultStyle,
}


def get_style_by_name(name: str) -> Style:
    try:
        return _STYLES[name.lower()]()
    except KeyError as exc:  # pragma: no cover
        raise ValueError(f"Unknown style {name!r}") from exc
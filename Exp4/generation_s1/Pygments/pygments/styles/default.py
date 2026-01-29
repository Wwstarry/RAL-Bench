from __future__ import annotations

from pygments.styles import Style
from pygments.token import (
    Token,
    Text,
    Comment,
    Keyword,
    Name,
    Literal,
    Operator,
    Punctuation,
    Error,
)


class DefaultStyle(Style):
    """
    A small, deterministic default style mapping.

    Style strings are a simplified subset of real Pygments style syntax:
    - "bold", "italic", "underline"
    - "#rrggbb" foreground color
    - "bg:#rrggbb" background color
    """

    background_color = "#f8f8f8"
    highlight_color = "#ffffcc"
    default_style = ""

    styles = {
        Token: "",
        Text: "",
        Error: "bold #ff0000",
        Comment: "italic #888888",
        Comment.Single: "italic #888888",
        Comment.Multiline: "italic #888888",
        Keyword: "bold #0000cc",
        Keyword.Constant: "bold #0000cc",
        Keyword.Type: "bold #0000cc",
        Name: "#000000",
        Name.Builtin: "#0033aa",
        Name.Function: "bold #0066aa",
        Name.Class: "bold #0066aa",
        Name.Decorator: "#6600aa",
        Name.Attribute: "#0055aa",
        Name.Namespace: "#0055aa",
        Literal.String: "#008800",
        Literal.String.Doc: "italic #008800",
        Literal.String.Escape: "bold #008800",
        Literal.Number: "#aa22ff",
        Operator: "#333333",
        Operator.Word: "bold #333333",
        Punctuation: "#333333",
    }


__all__ = ["DefaultStyle"]
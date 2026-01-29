"""
Provides the DefaultStyle definition.
"""

from ..token import Token, Keyword, Name, Comment, String, Number, Operator, Punctuation

class DefaultStyle:
    background_color = None
    default_style = ""

    styles = {
        Token: "",
        Comment: "italic #888",
        Keyword: "bold #005",
        Name: "#000",
        String: "#00f",
        Number: "#008",
        Operator: "#333",
        Punctuation: "#666",
    }
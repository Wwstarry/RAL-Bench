"""
A small, pure-Python subset of the Pygments API.

This repository is intentionally minimal but keeps the package/module layout
and key APIs used by common black-box tests.
"""
from __future__ import annotations

__version__ = "0.1"

from .token import (  # noqa: F401
    Token,
    TokenType,
    Text,
    Whitespace,
    Error,
    Other,
    Keyword,
    Name,
    Literal,
    String,
    Number,
    Operator,
    Punctuation,
    Comment,
    Generic,
)

from .util import ClassNotFound, OptionError  # noqa: F401
from .lex import lex  # noqa: F401
from .highlight import highlight  # noqa: F401

__all__ = [
    "__version__",
    "lex",
    "highlight",
    "ClassNotFound",
    "OptionError",
    # token exports
    "Token",
    "TokenType",
    "Text",
    "Whitespace",
    "Error",
    "Other",
    "Keyword",
    "Name",
    "Literal",
    "String",
    "Number",
    "Operator",
    "Punctuation",
    "Comment",
    "Generic",
]
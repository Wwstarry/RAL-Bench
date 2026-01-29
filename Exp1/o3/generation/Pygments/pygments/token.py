"""
Ultra-light replica of the Pygments token hierarchy.

Only a fraction of the original functionality is required for the test-suite.
"""

from __future__ import annotations

from typing import Dict, Tuple

__all__ = [
    "Token",
    "is_token_subtype",
]

###############################################################################
# Core token implementation
###############################################################################


class _TokenType(tuple):
    """
    Each token is represented as an *immutable* tuple of names.

    The root token (`Token`) is an empty tuple.  Accessing attributes on a
    token produces child tokens:

        Token.Name          -> Token.Name
        Token.Name.Function -> Token.Name.Function
    """

    _cache: Dict[Tuple[str, ...], "._TokenType"] = {}  # shared cache

    def __new__(cls, value=()):
        if not isinstance(value, tuple):
            raise TypeError("Token value must be a tuple")
        if value in cls._cache:
            return cls._cache[value]
        obj = super().__new__(cls, value)
        cls._cache[value] = obj
        return obj

    # --------------------------------------------------------------------- #
    # Magic methods
    # --------------------------------------------------------------------- #

    def __getattr__(self, name: str) -> "._TokenType":
        return _TokenType(self + (name,))

    def __repr__(self):
        return self._stringify()

    __str__ = __repr__

    # --------------------------------------------------------------------- #
    # Helpers
    # --------------------------------------------------------------------- #
    def _stringify(self) -> str:
        if not self:
            return "Token"
        return "Token." + ".".join(self)


# public root token
Token = _TokenType()


###############################################################################
# Standard token hierarchy shortcuts
###############################################################################

# Top-level groups (subset of official list)
Token.Text
Token.Whitespace
Token.Error
Token.Other
Token.Comment
Token.Keyword
Token.Name
Token.Literal
Token.String
Token.Number
Token.Operator
Token.Punctuation

# Nested (used by lexers/formatters below)
Token.Comment.Single
Token.Comment.Multiline
Token.Name.Function
Token.Name.Class
Token.Name.Builtin
Token.Literal.String.Double
Token.Literal.String.Single
Token.Literal.Number.Integer
Token.Literal.Number.Float
Token.Keyword.Constant

###############################################################################
# Utility functions
###############################################################################


def is_token_subtype(child: _TokenType, parent: _TokenType) -> bool:
    """
    Return ``True`` if *child* is equal to, or a sub-token of, *parent*.
    """
    if len(child) < len(parent):
        return False
    return child[: len(parent)] == parent
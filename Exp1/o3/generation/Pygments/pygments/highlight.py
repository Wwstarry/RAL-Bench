"""
A trimmed-down ``pygments.highlight`` helper that connects a lexer with a
formatter and returns the resulting string.
"""

from io import StringIO
from typing import List, Tuple, Union

from pygments.lex import lex
from pygments.token import Token

TokenStream = List[Tuple[Token, str]]  # for type checking


def highlight(code: str, lexer, formatter) -> str:
    """
    Apply *lexer* and *formatter* to *code* and return the highlighted output.
    """
    tokens = lex(code, lexer)
    out = StringIO()
    formatter.format(tokens, out)
    return out.getvalue()


__all__: List[str] = ["highlight"]
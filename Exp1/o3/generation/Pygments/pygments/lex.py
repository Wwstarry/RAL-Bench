"""
Lightweight implementation of the top-level ``pygments.lex`` helper.
"""

from typing import Iterable, List, Tuple, Union

from pygments.lexers import get_lexer_by_name
from pygments.token import Token

# A token stream is an iterator/generator of (tokentype, value) tuples.
TokenStream = Iterable[Tuple[Token, str]]


def lex(code: str, lexer: Union[str, "BaseLexer", type]) -> TokenStream:  # noqa: F821
    """
    High-level helper that returns a *token stream* for *code*.

    *lexer* may be
      - a lexer *instance*
      - a lexer *class*
      - a string (short name), forwarded to ``pygments.lexers.get_lexer_by_name``.
    """
    from pygments.lexers import BaseLexer  # local import to avoid circularity

    if isinstance(lexer, BaseLexer):
        instance = lexer
    elif isinstance(lexer, str):
        instance = get_lexer_by_name(lexer)
    elif isinstance(lexer, type) and issubclass(lexer, BaseLexer):
        instance = lexer()
    else:
        raise TypeError("Invalid lexer argument")

    return instance.get_tokens(code)


__all__: List[str] = ["lex", "TokenStream"]
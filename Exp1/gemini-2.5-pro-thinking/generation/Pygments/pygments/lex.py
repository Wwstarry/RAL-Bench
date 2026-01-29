"""
    pygments.lex
    ~~~~~~~~~~~~

    Lexer function.

    :copyright: Copyright 2006-2021 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from pygments.lexers import get_lexer_by_name


def lex(code, lexer):
    """
    Lex ``code`` with ``lexer`` and return an iterable of tokens.
    """
    return lexer.get_tokens(code)
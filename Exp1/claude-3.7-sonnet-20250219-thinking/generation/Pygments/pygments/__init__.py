# -*- coding: utf-8 -*-
"""
    pygments
    ~~~~~~~

    Pygments is a syntax highlighting package written in Python.

    :copyright: Copyright 2006-2023 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from pygments.lex import lex
from pygments.highlight import highlight
from pygments.lexers import get_lexer_by_name

__version__ = '2.14.0'
__all__ = ['lex', 'highlight', 'get_lexer_by_name']


def lex(code, lexer):
    """
    Lex the given code using the given lexer and return an iterable of tokens.
    """
    return lexer.get_tokens(code)
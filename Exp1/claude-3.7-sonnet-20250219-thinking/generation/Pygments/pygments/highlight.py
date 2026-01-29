# -*- coding: utf-8 -*-
"""
    pygments.highlight
    ~~~~~~~~~~~~~~~~

    Highlighting engine.

    :copyright: Copyright 2006-2023 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""


def highlight(code, lexer, formatter, outfile=None):
    """
    Highlight the source code using a lexer and formatter.

    :param code: source code to parse
    :param lexer: the lexer to use
    :param formatter: the formatter to use
    :param outfile: a file-like object to write the output to

    If `outfile` is not given, the result will be returned as a string.
    """
    tokens = lexer.get_tokens(code)
    if outfile:
        return formatter.format(tokens, outfile)
    else:
        return formatter.format(tokens)
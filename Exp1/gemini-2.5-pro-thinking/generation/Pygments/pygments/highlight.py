"""
    pygments.highlight
    ~~~~~~~~~~~~~~~~~~

    Highlight code to various formats.

    :copyright: Copyright 2006-2021 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import sys

from pygments.util import StringIO


def highlight(code, lexer, formatter, outfile=None):
    """
    Lex `code` with `lexer` and format it with the `formatter`.

    If `outfile` is given, the formatted code is written to it.
    Otherwise, it is returned as a string.
    """
    if outfile:
        formatter.format(lexer.get_tokens(code), outfile)
    else:
        string_io = StringIO()
        formatter.format(lexer.get_tokens(code), string_io)
        return string_io.getvalue()
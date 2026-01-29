"""
Core entry point to combine lexing and formatting.
"""

from io import StringIO
from .lex import lex

def highlight(code, lexer, formatter):
    """
    Convert `code` through `lexer` into text via `formatter`.
    """
    outfile = StringIO()
    formatter.format(lex(code, lexer), outfile)
    return outfile.getvalue()
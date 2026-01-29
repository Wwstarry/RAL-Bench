"""
Pygments - A pure-Python syntax highlighting library
"""

__version__ = '2.0.0'
__all__ = ['lex', 'highlight', 'format']

from pygments.lexers import get_lexer_by_name
from pygments.formatters import get_formatter_by_name
from pygments.lex import lex


def highlight(code, lexer, formatter):
    """
    Highlight code with the given lexer and formatter.
    
    Args:
        code: Source code string to highlight
        lexer: Lexer instance to tokenize the code
        formatter: Formatter instance to format the tokens
        
    Returns:
        Formatted output string
    """
    return formatter.format(lex(code, lexer), code)


def format(tokens, formatter):
    """
    Format a token stream with the given formatter.
    
    Args:
        tokens: Iterator of (tokentype, value) tuples
        formatter: Formatter instance
        
    Returns:
        Formatted output string
    """
    return formatter.format(tokens, None)
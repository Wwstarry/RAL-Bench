from pygments.lex import lex
from pygments.token import Token

def highlight(code, lexer, formatter):
    """
    Highlight the code by lexing it with the lexer and formatting with the formatter.
    Returns the formatted output as a string.
    """
    tokens = lex(code, lexer)
    return formatter.format(tokens)
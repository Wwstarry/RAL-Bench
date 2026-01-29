"""
Highlighting interface for Pygments.
"""


def highlight(code, lexer, formatter):
    """
    Highlight the given code using the provided lexer and formatter.
    
    Returns the formatted output as a string.
    """
    tokens = lexer.get_tokens(code)
    return formatter.format(tokens)
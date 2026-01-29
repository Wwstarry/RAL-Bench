"""
Lexing interface for Pygments.
"""


def lex(code, lexer):
    """
    Lex the given code using the provided lexer.
    
    Returns an iterator of (token_type, value) tuples.
    """
    return lexer.get_tokens(code)
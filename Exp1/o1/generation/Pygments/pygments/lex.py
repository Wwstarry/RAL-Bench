"""
Provides the lex(...) interface which applies a lexer to code and yields tokens.
"""

def lex(code, lexer, options=None):
    """
    Lex `code` using `lexer`. Yields (tokentype, text) tuples.
    """
    if options is None:
        options = {}
    yield from lexer.get_tokens(code, **options)
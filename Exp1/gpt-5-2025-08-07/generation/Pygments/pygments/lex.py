def lex(code, lexer):
    """
    Lex a piece of code and return a token stream.

    Parameters:
    - code: text to lex
    - lexer: a lexer instance

    Returns:
    - an iterator of (ttype, value) token pairs
    """
    if hasattr(lexer, "get_tokens"):
        return lexer.get_tokens(code)
    raise TypeError("Expected a lexer with get_tokens(code)")
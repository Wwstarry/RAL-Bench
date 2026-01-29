def highlight(code, lexer, formatter):
    """
    Lex code and format it using the given lexer and formatter.
    """
    tokens = lexer.get_tokens(code)
    return formatter.format(tokens, outfile=None)
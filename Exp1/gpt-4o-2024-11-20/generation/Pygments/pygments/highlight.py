def highlight(code, lexer, formatter):
    """
    Highlight the given code using the specified lexer and formatter.

    :param code: The source code to highlight.
    :param lexer: The lexer instance to use for tokenization.
    :param formatter: The formatter instance to use for output.
    :return: The formatted output as a string.
    """
    tokens = lexer.get_tokens(code)
    return formatter.format(tokens)
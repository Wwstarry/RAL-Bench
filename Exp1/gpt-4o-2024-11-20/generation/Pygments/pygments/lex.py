from pygments.token import Token

def lex(code, lexer):
    """
    Tokenize the given code using the specified lexer.

    :param code: The source code to tokenize.
    :param lexer: The lexer instance to use for tokenization.
    :return: A generator yielding (token_type, value) tuples.
    """
    return lexer.get_tokens(code)
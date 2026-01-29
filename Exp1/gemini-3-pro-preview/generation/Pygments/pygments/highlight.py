from pygments.lex import lex

def highlight(code, lexer, formatter, outfile=None):
    """
    Lex ``code`` with ``lexer`` and format it with the ``formatter``.
    """
    tokens = lex(code, lexer)
    return formatter.format(tokens, outfile)
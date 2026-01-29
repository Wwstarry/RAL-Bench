from pygments.token import Token
from pygments.lexers import get_lexer_by_name

def lex(code, lexer):
    """
    Return a token stream for code using the given lexer.
    """
    if hasattr(lexer, 'get_tokens'):
        return lexer.get_tokens(code)
    else:
        # Assume it's a lexer name
        lxr = get_lexer_by_name(lexer)
        return lxr.get_tokens(code)
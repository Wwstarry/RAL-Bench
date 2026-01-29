"""
Highlighting interface.
"""

__all__ = ['highlight']

def highlight(code, lexer, formatter):
    """Highlight code using lexer and formatter."""
    tokens = lexer.get_tokens(code)
    return formatter.format(tokens)
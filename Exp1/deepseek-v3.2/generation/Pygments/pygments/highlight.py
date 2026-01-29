"""
Highlighting interface.
"""

def highlight(code, lexer, formatter):
    """Highlight code using lexer and format with formatter."""
    tokens = lexer.get_tokens(code)
    return formatter.format(tokens, lexer)
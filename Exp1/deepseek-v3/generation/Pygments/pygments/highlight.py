"""Highlighting function that connects lexers to formatters."""

def highlight(code, lexer, formatter, **options):
    """Highlight code using the given lexer and formatter."""
    tokens = lexer.get_tokens(code)
    return formatter.format(tokens, **options)
import io

def highlight(code, lexer, formatter):
    """
    Connect lexing to formatting.

    Parameters:
    - code: input text
    - lexer: a lexer instance
    - formatter: a formatter instance

    Returns:
    - formatted string
    """
    # Allow passing names for convenience (not required by Pygments API, but handy)
    from .lexers import get_lexer_by_name
    from .formatters import get_formatter_by_name

    if isinstance(lexer, str):
        lexer = get_lexer_by_name(lexer)
    if isinstance(formatter, str):
        formatter = get_formatter_by_name(formatter)

    tokens = lexer.get_tokens(code)
    buf = io.StringIO()
    formatter.format(tokens, buf)
    return buf.getvalue()
"""
Minimal utility module for Pygments-like behaviors.
"""

class ClassNotFound(Exception):
    """Raised when a suitable lexer/formatter is not found."""
    pass

def option(value, default=None):
    """
    Basically returns 'value' if it's not None; otherwise 'default'.
    """
    return value if value is not None else default
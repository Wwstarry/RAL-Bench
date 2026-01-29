"""Utility functions and exceptions."""

class ClassNotFound(Exception):
    """Raised when a requested class is not found."""

def get_lexer_by_name(_alias, **options):
    """Get a lexer by its name or alias."""
    from pygments.lexers import get_lexer_by_name as _get_lexer_by_name
    return _get_lexer_by_name(_alias, **options)
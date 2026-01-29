"""
Utility functions.
"""

import re

__all__ = ['ClassNotFound', 'get_bool_opt', 'get_int_opt', 'get_list_opt', 'guess_lexer']

class ClassNotFound(Exception):
    """Raised when a class is not found."""
    pass

def get_bool_opt(options, key, default=False):
    """Get boolean option from dict."""
    return options.get(key, default)

def get_int_opt(options, key, default=0):
    """Get integer option from dict."""
    return options.get(key, default)

def get_list_opt(options, key, default=None):
    """Get list option from dict."""
    if default is None:
        default = []
    return options.get(key, default)

def guess_lexer(text, **options):
    """Guess lexer for given text."""
    # Simple implementation - just return PythonLexer
    from pygments.lexers.python import PythonLexer
    return PythonLexer(**options)
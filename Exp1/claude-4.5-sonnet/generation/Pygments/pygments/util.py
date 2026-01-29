"""
Utility functions and classes.
"""

import re


class ClassNotFound(ValueError):
    """Raised if a lexer, formatter or style is not found."""
    pass


def get_bool_opt(options, optname, default=None):
    """Get a boolean option from the options dict."""
    value = options.get(optname, default)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ('1', 'yes', 'true', 'on')
    return bool(value)


def get_int_opt(options, optname, default=None):
    """Get an integer option from the options dict."""
    value = options.get(optname, default)
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def get_list_opt(options, optname, default=None):
    """Get a list option from the options dict."""
    value = options.get(optname, default)
    if isinstance(value, str):
        return value.split()
    if isinstance(value, (list, tuple)):
        return list(value)
    return default or []


def docstring_headline(obj):
    """Get the first line of a docstring."""
    if not obj.__doc__:
        return ''
    return obj.__doc__.strip().split('\n')[0].strip()


def looks_like_xml(text):
    """Check if text looks like XML."""
    return bool(re.search(r'^\s*<\?xml', text, re.IGNORECASE))


def html_doctype_matches(text):
    """Check if text starts with an HTML doctype."""
    return bool(re.search(r'^\s*<!DOCTYPE\s+html', text, re.IGNORECASE))


def shebang_matches(text, regex):
    """Check if the shebang line matches the given regex."""
    lines = text.split('\n', 1)
    if lines and lines[0].startswith('#!'):
        return bool(re.search(regex, lines[0]))
    return False


def make_analysator(f):
    """Decorator to mark a function as an analysator."""
    f.analyse_text = True
    return f
"""
    pygments.util
    ~~~~~~~~~~~~~

    Utility functions.

    :copyright: Copyright 2006-2021 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re

try:
    from io import StringIO
except ImportError:
    from StringIO import StringIO


class ClassNotFound(ValueError):
    """Raised if a class cannot be found by name."""


def get_choice_opt(options, name, choices, default=None, normcase=False):
    """Get an option with a limited choice."""
    string = options.get(name, default)
    if not isinstance(string, str):
        return string
    if normcase:
        string = string.lower()
    if string in choices:
        return string
    # for backwards compatibility, check ``'True'`` and ``'False'``
    if string == 'True':
        return True
    elif string == 'False':
        return False
    raise ValueError("Value for option %s must be one of %s, not %r" %
                     (name, ", ".join(map(str, choices)), string))


def get_bool_opt(options, name, default=False):
    """Get a boolean option."""
    string = options.get(name, default)
    if isinstance(string, bool):
        return string
    elif isinstance(string, int):
        return bool(string)
    elif not isinstance(string, str):
        return string
    if string.lower() in ('1', 'true', 'yes', 'on'):
        return True
    elif string.lower() in ('0', 'false', 'no', 'off'):
        return False
    else:
        return default


def get_int_opt(options, name, default=0):
    """Get an integer option."""
    string = options.get(name, default)
    if isinstance(string, int):
        return string
    elif not isinstance(string, str):
        return string
    try:
        return int(string)
    except ValueError:
        return default


def docstring_headline(obj):
    if not obj.__doc__:
        return ''
    return obj.__doc__.strip().splitlines()[0]


def shebang_matches(text, regex):
    """
    Check if the first line of `text` matches `regex`.
    """
    if isinstance(regex, str):
        regex = re.compile(regex, re.VERBOSE)
    first_line = text.splitlines()[0] if text else ''
    if first_line.startswith('#!'):
        return regex.search(first_line) is not None
    return False


def looks_like_xml(text):
    """
    Check if `text` looks like XML.
    """
    # This is a simplified check
    text = text.lstrip()
    return text.startswith('<') and text.endswith('>')
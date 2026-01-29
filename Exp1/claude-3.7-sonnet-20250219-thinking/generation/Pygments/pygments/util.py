# -*- coding: utf-8 -*-
"""
    pygments.util
    ~~~~~~~~~~~~

    Utility functions.

    :copyright: Copyright 2006-2023 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re
import sys


class ClassNotFound(ValueError):
    """Raised if a lexer, formatter or filter class is not found."""


def get_choice_opt(options, optname, allowed, default=None, normcase=False):
    """Return a value from the options dict, checking if it's in the allowed list.

    If normcase is true, the value is normalized to lowercase before checking.
    """
    string = options.get(optname, default)
    if string is None:
        return default
    if normcase:
        string = string.lower()
    if string not in allowed:
        raise ValueError("Value for %r must be one of %r" % (optname, allowed))
    return string


def get_bool_opt(options, optname, default=None):
    """Return a boolean value from the options dict.

    The value can be a boolean or a string. If the string is "true" or "yes",
    return True. If the string is "false" or "no", return False. Otherwise
    raise an exception.
    """
    string = options.get(optname, default)
    if string is None:
        return default
    if isinstance(string, bool):
        return string
    if isinstance(string, str):
        string = string.lower()
        if string in ('yes', 'true', '1'):
            return True
        if string in ('no', 'false', '0'):
            return False
    raise ValueError("Value for %r must be a boolean" % optname)


def get_int_opt(options, optname, default=None):
    """Return an integer value from the options dict.

    The value can be an integer or a string. If the string represents an integer,
    return that integer. Otherwise raise an exception.
    """
    string = options.get(optname, default)
    if string is None:
        return default
    if isinstance(string, int):
        return string
    if isinstance(string, str):
        try:
            return int(string)
        except ValueError:
            pass
    raise ValueError("Value for %r must be an integer" % optname)


def make_analysator(f):
    """Return a static text analyser function for `f`.

    `f` is a function that takes a string and returns a float between 0.0 and 1.0.
    If the analyser returns 1.0, it's taken to be a perfect match.
    """
    def wrapper(text):
        try:
            return f(text)
        except Exception:
            return 0.0
    return wrapper


def shebang_matches(text, regex):
    """Check if the given regular expression matches the first line of the text."""
    if not text:
        return False
    first_line = text.splitlines()[0]
    return bool(re.match(regex, first_line))
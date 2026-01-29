# -*- coding: utf-8 -*-
"""
    pygments.lexers
    ~~~~~~~~~~~~~

    Lexer classes and groups.

    :copyright: Copyright 2006-2023 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from pygments.util import ClassNotFound

# Dictionary that maps language names to their lexer classes
LEXERS = {}


def register_lexer(name, aliases, filenames, mimetypes, cls):
    """
    Register a lexer class under the name ``name``.
    """
    LEXERS[name] = cls
    for alias in aliases:
        LEXERS[alias] = cls


def get_lexer_by_name(name, **options):
    """
    Return a lexer by name or alias.
    """
    if name not in LEXERS:
        # Import built-in lexers to populate the LEXERS dictionary
        from pygments.lexers.python import PythonLexer
        from pygments.lexers.json import JsonLexer
        from pygments.lexers.ini import IniLexer
    
    if name not in LEXERS:
        raise ClassNotFound("No lexer for name %r found" % name)
    
    return LEXERS[name](**options)


# Add the basic lexers
from pygments.lexers.python import PythonLexer
from pygments.lexers.json import JsonLexer
from pygments.lexers.ini import IniLexer

# Register them
register_lexer('python', ['python', 'py'], ['*.py'], ['text/x-python', 'application/x-python'], PythonLexer)
register_lexer('json', ['json'], ['*.json'], ['application/json'], JsonLexer)
register_lexer('ini', ['ini', 'cfg', 'conf'], ['*.ini', '*.cfg', '*.conf'], ['text/x-ini'], IniLexer)
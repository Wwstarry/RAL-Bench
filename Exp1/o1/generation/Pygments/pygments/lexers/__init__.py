"""
Provides the get_lexer_by_name and registers minimal lexers.
"""

from ..util import ClassNotFound
from .python import PythonLexer
from .json import JsonLexer
from .ini import IniLexer

_lexers_by_name = {
    "python": PythonLexer,
    "py": PythonLexer,
    "json": JsonLexer,
    "ini": IniLexer,
    "cfg": IniLexer,
}

def get_lexer_by_name(name, **options):
    """
    Return an instance of a lexer matching `name`.
    Raise ClassNotFound if no lexer is found.
    """
    name = name.lower()
    if name in _lexers_by_name:
        return _lexers_by_name[name](**options)
    raise ClassNotFound("No lexer for name %r found." % name)
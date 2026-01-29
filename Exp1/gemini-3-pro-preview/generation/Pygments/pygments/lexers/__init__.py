from pygments.util import ClassNotFound
from pygments.lexers.python import PythonLexer
from pygments.lexers.json import JsonLexer
from pygments.lexers.ini import IniLexer

_LEXER_REGISTRY = {
    'python': PythonLexer,
    'py': PythonLexer,
    'json': JsonLexer,
    'ini': IniLexer,
    'cfg': IniLexer,
}

def get_lexer_by_name(_alias, **options):
    cls = _LEXER_REGISTRY.get(_alias.lower())
    if cls:
        return cls(**options)
    raise ClassNotFound("No lexer found for name %r" % _alias)

__all__ = ['get_lexer_by_name', 'PythonLexer', 'JsonLexer', 'IniLexer']
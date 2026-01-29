from ..util import ClassNotFound
from .python import PythonLexer
from .json import JsonLexer
from .ini import IniLexer

_lexer_by_name = {
    "python": PythonLexer,
    "py": PythonLexer,
    "json": JsonLexer,
    "ini": IniLexer,
    "cfg": IniLexer,
}

def get_lexer_by_name(name, **options):
    """
    Return a lexer instance by short name.
    """
    cls = _lexer_by_name.get(name.lower())
    if not cls:
        raise ClassNotFound(f"No lexer for name '{name}'")
    return cls(**options)

def find_lexer_class_by_name(name):
    return _lexer_by_name.get(name.lower())
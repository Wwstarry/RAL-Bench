from .python import PythonLexer
from .json import JsonLexer
from .ini import IniLexer

_lexers = {
    'python': PythonLexer,
    'py': PythonLexer,
    'json': JsonLexer,
    'ini': IniLexer,
}

def get_lexer_by_name(name):
    name = name.lower()
    if name not in _lexers:
        raise ValueError(f"No lexer found for name '{name}'")
    return _lexers[name]()
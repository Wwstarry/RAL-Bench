"""
Lexers for various languages and formats.
"""

from pygments.util import ClassNotFound


def get_lexer_by_name(name):
    """Get a lexer by its name."""
    name_lower = name.lower()
    
    if name_lower in ('python', 'py'):
        from pygments.lexers.python import PythonLexer
        return PythonLexer()
    elif name_lower in ('json',):
        from pygments.lexers.json import JsonLexer
        return JsonLexer()
    elif name_lower in ('ini', 'cfg', 'conf'):
        from pygments.lexers.ini import IniLexer
        return IniLexer()
    else:
        raise ClassNotFound(f"No lexer found for name {name!r}")


def get_lexer_by_filename(filename):
    """Get a lexer by filename."""
    if filename.endswith('.py'):
        from pygments.lexers.python import PythonLexer
        return PythonLexer()
    elif filename.endswith('.json'):
        from pygments.lexers.json import JsonLexer
        return JsonLexer()
    elif filename.endswith(('.ini', '.cfg', '.conf')):
        from pygments.lexers.ini import IniLexer
        return IniLexer()
    else:
        raise ClassNotFound(f"No lexer found for filename {filename!r}")


__all__ = ['get_lexer_by_name', 'get_lexer_by_filename']
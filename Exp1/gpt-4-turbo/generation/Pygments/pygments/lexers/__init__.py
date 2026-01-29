from pygments.util import ClassNotFound

_lexer_map = {}

def get_lexer_by_name(name, **options):
    name = name.lower()
    if not _lexer_map:
        # Lazy import to avoid circular imports
        from pygments.lexers.python import PythonLexer
        from pygments.lexers.json import JsonLexer
        from pygments.lexers.ini import IniLexer
        _lexer_map['python'] = PythonLexer
        _lexer_map['py'] = PythonLexer
        _lexer_map['json'] = JsonLexer
        _lexer_map['ini'] = IniLexer
    try:
        return _lexer_map[name](**options)
    except KeyError:
        raise ClassNotFound("No lexer for alias %r found" % name)
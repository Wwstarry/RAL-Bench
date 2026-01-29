"""
Lexer registry and lookup functions.
"""

from pygments.util import ClassNotFound


_lexer_cache = {}


def get_lexer_by_name(name, **options):
    """
    Get a lexer by its short name.
    
    Args:
        name: Short name of the lexer (e.g., 'python', 'json')
        **options: Options to pass to the lexer
        
    Returns:
        Lexer instance
        
    Raises:
        ClassNotFound: If no lexer with that name exists
    """
    name = name.lower()
    
    # Import lexers on demand
    if name == 'python' or name == 'py':
        from pygments.lexers.python import PythonLexer
        return PythonLexer(**options)
    elif name == 'json':
        from pygments.lexers.json import JsonLexer
        return JsonLexer(**options)
    elif name == 'ini' or name == 'cfg':
        from pygments.lexers.ini import IniLexer
        return IniLexer(**options)
    else:
        raise ClassNotFound(f'No lexer found for name {name!r}')


def get_all_lexers():
    """
    Return a generator of all available lexers.
    
    Yields:
        (name, aliases, filenames, mimetypes) tuples
    """
    from pygments.lexers.python import PythonLexer
    from pygments.lexers.json import JsonLexer
    from pygments.lexers.ini import IniLexer
    
    for lexer_cls in [PythonLexer, JsonLexer, IniLexer]:
        yield (lexer_cls.name, lexer_cls.aliases, 
               lexer_cls.filenames, lexer_cls.mimetypes)


def find_lexer_class(name):
    """
    Find a lexer class by name.
    
    Args:
        name: Name of the lexer
        
    Returns:
        Lexer class or None
    """
    name = name.lower()
    
    if name in ('python', 'py'):
        from pygments.lexers.python import PythonLexer
        return PythonLexer
    elif name == 'json':
        from pygments.lexers.json import JsonLexer
        return JsonLexer
    elif name in ('ini', 'cfg'):
        from pygments.lexers.ini import IniLexer
        return IniLexer
    
    return None
"""
Lexer package.
"""

import re
from pygments.lexer import Lexer, RegexLexer
from pygments.token import Token
from pygments.util import ClassNotFound

__all__ = ['get_lexer_by_name', 'guess_lexer']

_lexer_cache = {}

def _load_lexers():
    """Load all lexers."""
    from pygments.lexers.python import PythonLexer
    from pygments.lexers.json import JsonLexer
    from pygments.lexers.ini import IniLexer
    
    return {
        'python': PythonLexer,
        'json': JsonLexer,
        'ini': IniLexer,
    }

def get_lexer_by_name(name, **options):
    """Get lexer by name."""
    if not _lexer_cache:
        _lexer_cache.update(_load_lexers())
    
    name = name.lower()
    if name in _lexer_cache:
        return _lexer_cache[name](**options)
    raise ClassNotFound(f"No lexer for alias {name!r} found")

def guess_lexer(text, **options):
    """Guess lexer for given text."""
    # Simple implementation - check for shebang or file extension
    if text.startswith('#!'):
        if 'python' in text.split('\n')[0]:
            return get_lexer_by_name('python', **options)
    
    # Check for JSON
    text_strip = text.strip()
    if text_strip.startswith('{') or text_strip.startswith('['):
        try:
            import json
            json.loads(text)
            return get_lexer_by_name('json', **options)
        except:
            pass
    
    # Default to Python
    return get_lexer_by_name('python', **options)
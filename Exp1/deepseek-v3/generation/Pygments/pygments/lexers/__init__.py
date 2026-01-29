"""Lexer registry and discovery."""

import sys
from pygments.lexers.python import PythonLexer
from pygments.lexers.json import JsonLexer
from pygments.lexers.ini import IniLexer

# Registry of available lexers
_lexer_cache = {}

def _load_lexers():
    """Load all available lexers."""
    lexers = [
        PythonLexer,
        JsonLexer,
        IniLexer,
    ]
    
    for lexer_class in lexers:
        _lexer_cache[lexer_class.name.lower()] = lexer_class
        for alias in getattr(lexer_class, 'aliases', []):
            _lexer_cache[alias.lower()] = lexer_class

def get_lexer_by_name(alias, **options):
    """Get a lexer by name or alias."""
    if not _lexer_cache:
        _load_lexers()
    
    alias_lower = alias.lower()
    if alias_lower in _lexer_cache:
        lexer_class = _lexer_cache[alias_lower]
        return lexer_class(**options)
    
    raise ClassNotFound(f"No lexer found for alias '{alias}'")

# Initialize on import
_load_lexers()
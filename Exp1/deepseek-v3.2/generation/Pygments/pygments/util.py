"""
Utility functions.
"""

import re
from pygments.lexers import get_lexer_by_name

class ClassNotFound(Exception):
    """Raised when a requested class is not found."""
    pass

def get_lexer_for_filename(filename, **options):
    """Get a lexer for a filename."""
    # Simple implementation - just check extension
    if filename.endswith('.py'):
        return get_lexer_by_name('python', **options)
    elif filename.endswith('.json'):
        return get_lexer_by_name('json', **options)
    elif filename.endswith('.ini'):
        return get_lexer_by_name('ini', **options)
    raise ClassNotFound(f"No lexer found for file '{filename}'")

def get_lexer_for_mimetype(mimetype, **options):
    """Get a lexer for a mimetype."""
    if mimetype == 'application/json':
        return get_lexer_by_name('json', **options)
    elif mimetype == 'text/x-python':
        return get_lexer_by_name('python', **options)
    raise ClassNotFound(f"No lexer found for mimetype '{mimetype}'")

def guess_lexer(text, **options):
    """Guess a lexer for the given text."""
    # Simple heuristic: check for Python shebang or keywords
    if text.startswith('#!') and 'python' in text.split('\n')[0].lower():
        return get_lexer_by_name('python', **options)
    # Check for JSON
    if text.strip().startswith('{') or text.strip().startswith('['):
        try:
            import json
            json.loads(text)
            return get_lexer_by_name('json', **options)
        except:
            pass
    # Default to Python
    return get_lexer_by_name('python', **options)
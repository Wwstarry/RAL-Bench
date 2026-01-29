"""A pure-Python syntax highlighting library compatible with Pygments API."""

from pygments.lex import lex
from pygments.highlight import highlight
from pygments.token import Token, STANDARD_TYPES
from pygments.util import ClassNotFound, get_lexer_by_name
from pygments.lexers import get_lexer_by_name as _get_lexer_by_name
from pygments.formatters import get_formatter_by_name
from pygments.styles import get_style_by_name

__all__ = [
    'lex', 'highlight', 'Token', 'STANDARD_TYPES', 
    'ClassNotFound', 'get_lexer_by_name', 'get_formatter_by_name',
    'get_style_by_name'
]
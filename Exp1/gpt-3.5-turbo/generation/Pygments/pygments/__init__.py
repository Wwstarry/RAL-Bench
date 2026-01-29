from .lex import lex
from .highlight import highlight
from .lexers import get_lexer_by_name
from .formatters import HtmlFormatter, TerminalFormatter
from .styles import default

__all__ = [
    'lex',
    'highlight',
    'get_lexer_by_name',
    'HtmlFormatter',
    'TerminalFormatter',
    'default',
]
# Minimal Pygments-like API compatibility layer

from .highlight import highlight
from .lex import lex
from .token import Token
from .util import ClassNotFound

# expose lexers and formatters helpers
from .lexers import get_lexer_by_name, PythonLexer, JsonLexer, IniLexer
from .formatters import HtmlFormatter, TerminalFormatter
from .styles import get_style_by_name

__version__ = "0.0.1"

__all__ = [
    "highlight",
    "lex",
    "Token",
    "ClassNotFound",
    "get_lexer_by_name",
    "PythonLexer",
    "JsonLexer",
    "IniLexer",
    "HtmlFormatter",
    "TerminalFormatter",
    "get_style_by_name",
]
"""JSON lexer implementation."""

import re
from pygments.lexer import RegexLexer
from pygments.token import Token

class JsonLexer(RegexLexer):
    """Lexer for JSON data."""
    
    name = 'JSON'
    aliases = ['json']
    filenames = ['*.json']
    mimetypes = ['application/json']
    
    flags = re.MULTILINE
    
    tokens = {
        'root': [
            (r'\s+', Token.Text),
            (r'"(\\\\|\\"|[^"])*"', Token.String.Double),
            (r'-?(0|[1-9]\d*)', Token.Number.Integer),
            (r'-?\d+\.\d+([eE][+-]?\d+)?', Token.Number.Float),
            (r'true|false|null', Token.Keyword.Constant),
            (r'[{}\[\],:]', Token.Punctuation),
        ],
    }
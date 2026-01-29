"""
JSON lexer.
"""

import re
from pygments.lexer import RegexLexer
from pygments.token import Token

__all__ = ['JsonLexer']

class JsonLexer(RegexLexer):
    """Lexer for JSON code."""
    
    name = 'JSON'
    aliases = ['json']
    filenames = ['*.json']
    
    tokens = {
        'root': [
            (r'\s+', Token.Text.Whitespace),
            (r'"(\\\\|\\"|[^"])*"', Token.Literal.String.Double),
            (r'-?\d+\.?\d*([eE][+-]?\d+)?', Token.Literal.Number),
            (r'\b(true|false|null)\b', Token.Keyword.Constant),
            (r'[{}[\],:]', Token.Punctuation),
            (r'.', Token.Text),
        ]
    }
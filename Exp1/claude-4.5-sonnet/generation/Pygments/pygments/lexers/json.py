"""
Lexer for JSON data.
"""

import re
from pygments.lex import RegexLexer
from pygments.token import (
    Text, String, Number, Keyword, Name, Punctuation, 
    Error, Whitespace
)


class JsonLexer(RegexLexer):
    """
    Lexer for JSON data.
    """
    
    name = 'JSON'
    aliases = ['json']
    filenames = ['*.json']
    mimetypes = ['application/json']
    
    flags = re.MULTILINE | re.DOTALL
    
    tokens = {
        'root': [
            (re.compile(r'\s+'), Whitespace, None),
            (re.compile(r'"'), String.Double, 'string'),
            (re.compile(r'-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?'), Number, None),
            (re.compile(r'\btrue\b'), Keyword.Constant, None),
            (re.compile(r'\bfalse\b'), Keyword.Constant, None),
            (re.compile(r'\bnull\b'), Keyword.Constant, None),
            (re.compile(r'[{\[:]'), Punctuation, None),
            (re.compile(r'[}\],]'), Punctuation, None),
            (re.compile(r'.'), Error, None),
        ],
        'string': [
            (re.compile(r'\\["\\/bfnrt]'), String.Escape, None),
            (re.compile(r'\\u[0-9a-fA-F]{4}'), String.Escape, None),
            (re.compile(r'[^"\\]+'), String.Double, None),
            (re.compile(r'"'), String.Double, '#pop'),
        ],
    }
    
    def analyse_text(text):
        """Check if text looks like JSON."""
        text = text.strip()
        if text.startswith('{') or text.startswith('['):
            return 0.8
        return 0.0
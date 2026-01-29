"""
Lexer for INI/CFG configuration files.
"""

import re
from pygments.lex import RegexLexer
from pygments.token import (
    Text, Comment, Keyword, Name, String, Operator,
    Punctuation, Whitespace
)


class IniLexer(RegexLexer):
    """
    Lexer for INI and CFG configuration files.
    """
    
    name = 'INI'
    aliases = ['ini', 'cfg']
    filenames = ['*.ini', '*.cfg', '*.properties']
    mimetypes = ['text/x-ini']
    
    flags = re.MULTILINE
    
    tokens = {
        'root': [
            (re.compile(r'\s+'), Whitespace, None),
            (re.compile(r'[;#].*$'), Comment.Single, None),
            (re.compile(r'\[([^\]]+)\]'), Keyword, None),
            (re.compile(r'([a-zA-Z_][a-zA-Z0-9_.\-]*)\s*([:=])'), 
             bygroups(Name.Attribute, Operator), 'value'),
            (re.compile(r'.'), Text, None),
        ],
        'value': [
            (re.compile(r'\n'), Whitespace, '#pop'),
            (re.compile(r'"[^"]*"'), String.Double, None),
            (re.compile(r"'[^']*'"), String.Single, None),
            (re.compile(r'[^\n]+'), String, None),
        ],
    }
    
    def analyse_text(text):
        """Check if text looks like an INI file."""
        score = 0.0
        if re.search(r'^\[[^\]]+\]', text, re.MULTILINE):
            score += 0.5
        if re.search(r'^[a-zA-Z_][a-zA-Z0-9_.\-]*\s*[:=]', text, re.MULTILINE):
            score += 0.3
        return min(score, 1.0)
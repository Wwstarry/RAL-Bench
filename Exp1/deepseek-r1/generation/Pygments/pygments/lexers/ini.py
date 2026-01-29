"""
INI lexer.
"""

import re
from pygments.lexer import RegexLexer
from pygments.token import Token

__all__ = ['IniLexer']

class IniLexer(RegexLexer):
    """Lexer for INI files."""
    
    name = 'INI'
    aliases = ['ini', 'cfg']
    filenames = ['*.ini', '*.cfg']
    
    tokens = {
        'root': [
            (r'\s+', Token.Text.Whitespace),
            (r'[;#].*', Token.Comment.Single),
            (r'\[.*?\]', Token.Name.Tag),
            (r'(.*?)(\s*)(=)(\s*)(.*)', 
             (Token.Name.Property, Token.Text, Token.Operator, Token.Text, 
              Token.Literal.String)),
            (r'.', Token.Text),
        ]
    }
"""INI file lexer implementation."""

import re
from pygments.lexer import RegexLexer
from pygments.token import Token

class IniLexer(RegexLexer):
    """Lexer for INI configuration files."""
    
    name = 'INI'
    aliases = ['ini', 'cfg']
    filenames = ['*.ini', '*.cfg']
    mimetypes = ['text/x-ini']
    
    tokens = {
        'root': [
            (r'\s+', Token.Text),
            (r'[;#].*', Token.Comment),
            (r'\[.*?\]', Token.Name.Tag),
            (r'(.*?)(\s*)(=)(\s*)(.*)', 
             bygroups(Token.Name.Property, Token.Text, Token.Operator, 
                     Token.Text, Token.String)),
            (r'.+', Token.String),
        ],
    }
    
    def bygroups(*args):
        """Helper to assign different tokens to capture groups."""
        def callback(lexer, match, context=None):
            for i, token_type in enumerate(args):
                if i * 2 + 1 < len(match.groups()):
                    value = match.group(i * 2 + 1)
                    if value:
                        yield match.start(i * 2 + 1), token_type, value
        return callback

IniLexer.tokens['root'][3] = (r'(.*?)(\s*)(=)(\s*)(.*)', 
                             IniLexer.bygroups(Token.Name.Property, Token.Text, 
                                             Token.Operator, Token.Text, Token.String))
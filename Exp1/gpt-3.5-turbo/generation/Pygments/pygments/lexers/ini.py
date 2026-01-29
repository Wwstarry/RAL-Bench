import re
from pygments.lex import RegexLexer
from pygments.token import *

class IniLexer(RegexLexer):
    name = 'INI'
    aliases = ['ini', 'cfg', 'conf']
    filenames = ['*.ini', '*.cfg', '*.conf']

    tokens = {
        'root': [
            (r'\s+', Whitespace),
            (r';.*$', Comment.Single),
            (r'\[.*?\]', Name.Namespace),
            (r'[^=;\s]+(?=\s*=)', Name.Attribute),
            (r'=', Operator),
            (r'.*$', String),
        ],
    }
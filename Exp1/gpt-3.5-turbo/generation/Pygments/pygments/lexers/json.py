import re
from pygments.lex import RegexLexer
from pygments.token import *

class JsonLexer(RegexLexer):
    name = 'JSON'
    aliases = ['json']
    filenames = ['*.json']

    tokens = {
        'root': [
            (r'\s+', Whitespace),
            (r'//.*?$', Comment.Single),
            (r'/\*.*?\*/', Comment.Multiline),
            (r'true|false|null', Keyword.Constant),
            (r'"(\\\\|\\"|[^"])*"', String.Double),
            (r'-?\d+\.\d+([eE][+-]?\d+)?', Number.Float),
            (r'-?\d+([eE][+-]?\d+)?', Number.Integer),
            (r'[{}\[\],:]', Punctuation),
        ],
    }
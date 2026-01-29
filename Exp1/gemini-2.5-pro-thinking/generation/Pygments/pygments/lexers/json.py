"""
    pygments.lexers.json
    ~~~~~~~~~~~~~~~~~~~~

    Lexers for JSON and related formats.

    :copyright: Copyright 2006-2021 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from pygments.lexer import RegexLexer, bygroups
from pygments.token import Punctuation, Keyword, Name, String, Number, Text

__all__ = ['JsonLexer']


class JsonLexer(RegexLexer):
    """
    For JSON data structures.
    """
    name = 'JSON'
    aliases = ['json']
    filenames = ['*.json']
    mimetypes = ['application/json']

    tokens = {
        'root': [
            (r'\s+', Text),
            (r'\{', Punctuation, 'object-members'),
            (r'\[', Punctuation, 'array-elements'),
        ],
        'object-members': [
            (r'"(\\"|[^"])*?"', Name.Tag, 'member-value'),
            (r'\}', Punctuation, '#pop'),
        ],
        'member-value': [
            (r':', Punctuation, 'value'),
        ],
        'array-elements': [
            (r',', Punctuation),
            (r']', Punctuation, '#pop'),
            ('', Text, 'value'),
        ],
        'value': [
            (r'\s+', Text),
            (r'"(\\"|[^"])*?"', String.Double),
            (r'(-?)(\d+)(\.\d+)?([eE][+-]?\d+)?', Number),
            (r'(true|false|null)\b', Keyword.Constant),
            (r'\{', Punctuation, 'object-members'),
            (r'\[', Punctuation, 'array-elements'),
            (r',', Punctuation, '#pop'),
            (r'\}', Punctuation, '#pop:2'),
            (r']', Punctuation, '#pop:2'),
        ],
    }
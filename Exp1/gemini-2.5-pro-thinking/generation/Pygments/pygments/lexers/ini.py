"""
    pygments.lexers.ini
    ~~~~~~~~~~~~~~~~~~~

    Lexers for configuration file formats.

    :copyright: Copyright 2006-2021 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from pygments.lexer import RegexLexer
from pygments.token import Text, Comment, Keyword, Name, String, Punctuation

__all__ = ['IniLexer']


class IniLexer(RegexLexer):
    """
    Lexer for configuration files in INI style.
    """
    name = 'INI'
    aliases = ['ini', 'cfg']
    filenames = ['*.ini', '*.cfg', '*.inf']
    mimetypes = ['text/x-ini', 'text/inf']

    tokens = {
        'root': [
            (r'\s+', Text),
            (r'[;#].*$', Comment.Single),
            (r'\[.*?\]', Keyword),
            (r'(.+?)(\s*)(=)(\s*)(.*)$', [
                (Name.Attribute, r'\1'),
                (Text, r'\2'),
                (Punctuation, r'\3'),
                (Text, r'\4'),
                (String, r'\5'),
            ]),
        ],
    }
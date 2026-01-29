"""
INI/Config file lexer.
"""

import re
from pygments.token import (
    Token, Text, Whitespace, Comment, Keyword, Name, String, Punctuation, Error
)


class IniLexer:
    """Lexer for INI/Config files."""
    
    name = 'INI'
    aliases = ['ini', 'cfg', 'conf']
    filenames = ['*.ini', '*.cfg', '*.conf']
    
    def get_tokens(self, code):
        """Tokenize INI file."""
        for line in code.split('\n'):
            pos = 0
            length = len(line)
            
            # Whitespace at start
            match = re.match(r'^[ \t]*', line)
            if match and match.group(0):
                yield (Whitespace, match.group(0))
                pos = len(match.group(0))
            
            # Comments
            if pos < length and line[pos] == ';':
                yield (Comment.Single, line[pos:])
                yield (Text, '\n')
                continue
            
            if pos < length and line[pos] == '#':
                yield (Comment.Single, line[pos:])
                yield (Text, '\n')
                continue
            
            # Section headers
            if pos < length and line[pos] == '[':
                match = re.match(r'\[([^\]]+)\]', line[pos:])
                if match:
                    yield (Punctuation, '[')
                    yield (Name, match.group(1))
                    yield (Punctuation, ']')
                    pos += len(match.group(0))
                    if pos < length:
                        yield (Text, line[pos:])
                    yield (Text, '\n')
                    continue
            
            # Key-value pairs
            match = re.match(r'([^=:]+)([:=])(.*)$', line[pos:])
            if match:
                key = match.group(1).rstrip()
                sep = match.group(2)
                value = match.group(3)
                
                yield (Name, key)
                yield (Whitespace, line[pos + len(key):pos + len(key) + len(sep) - len(sep.lstrip())])
                yield (Punctuation, sep)
                yield (Whitespace, line[pos + len(key) + len(sep):pos + len(key) + len(sep) + len(value) - len(value.lstrip())])
                yield (String, value.lstrip())
                yield (Text, '\n')
                continue
            
            # Remaining content
            if pos < length:
                yield (Text, line[pos:])
            yield (Text, '\n')
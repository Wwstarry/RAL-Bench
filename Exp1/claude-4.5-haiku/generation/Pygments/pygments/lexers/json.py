"""
JSON lexer.
"""

import re
from pygments.token import (
    Token, Text, Whitespace, String, Number, Keyword, Punctuation, Error
)


class JsonLexer:
    """Lexer for JSON."""
    
    name = 'JSON'
    aliases = ['json']
    filenames = ['*.json']
    
    def get_tokens(self, code):
        """Tokenize JSON."""
        pos = 0
        length = len(code)
        
        while pos < length:
            # Whitespace
            match = re.match(r'[ \t\r\n]+', code[pos:])
            if match:
                yield (Whitespace, match.group(0))
                pos += len(match.group(0))
                continue
            
            # Strings
            if code[pos] == '"':
                match = re.match(r'"(?:\\.|[^\\"])*"', code[pos:])
                if match:
                    yield (String.Double, match.group(0))
                    pos += len(match.group(0))
                    continue
            
            # Numbers
            match = re.match(r'-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?', code[pos:])
            if match:
                yield (Number.Integer, match.group(0))
                pos += len(match.group(0))
                continue
            
            # Keywords (true, false, null)
            match = re.match(r'(true|false|null)', code[pos:])
            if match:
                yield (Keyword, match.group(0))
                pos += len(match.group(0))
                continue
            
            # Punctuation
            if code[pos] in '{}[]:,':
                yield (Punctuation, code[pos])
                pos += 1
                continue
            
            # Unknown
            yield (Error, code[pos])
            pos += 1
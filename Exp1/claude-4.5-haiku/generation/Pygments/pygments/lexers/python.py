"""
Python lexer.
"""

import re
from pygments.token import (
    Token, Text, Whitespace, Comment, Operator, Keyword, Name, String,
    Number, Punctuation, Error
)


class PythonLexer:
    """Lexer for Python source code."""
    
    name = 'Python'
    aliases = ['python', 'py']
    filenames = ['*.py']
    
    KEYWORDS = {
        'False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await',
        'break', 'class', 'continue', 'def', 'del', 'elif', 'else', 'except',
        'finally', 'for', 'from', 'global', 'if', 'import', 'in', 'is',
        'lambda', 'nonlocal', 'not', 'or', 'pass', 'raise', 'return', 'try',
        'while', 'with', 'yield'
    }
    
    BUILTINS = {
        'abs', 'all', 'any', 'ascii', 'bin', 'bool', 'breakpoint', 'bytearray',
        'bytes', 'callable', 'chr', 'classmethod', 'compile', 'complex',
        'delattr', 'dict', 'dir', 'divmod', 'enumerate', 'eval', 'exec',
        'filter', 'float', 'format', 'frozenset', 'getattr', 'globals',
        'hasattr', 'hash', 'hex', 'id', 'input', 'int', 'isinstance',
        'issubclass', 'iter', 'len', 'list', 'locals', 'map', 'max',
        'memoryview', 'min', 'next', 'object', 'oct', 'open', 'ord', 'pow',
        'print', 'property', 'range', 'repr', 'reversed', 'round', 'set',
        'setattr', 'slice', 'sorted', 'staticmethod', 'str', 'sum', 'super',
        'tuple', 'type', 'vars', 'zip'
    }
    
    def get_tokens(self, code):
        """Tokenize Python source code."""
        pos = 0
        length = len(code)
        
        while pos < length:
            # Whitespace
            match = re.match(r'[ \t\r\n]+', code[pos:])
            if match:
                yield (Whitespace, match.group(0))
                pos += len(match.group(0))
                continue
            
            # Comments
            if code[pos:pos+1] == '#':
                match = re.match(r'#[^\n]*', code[pos:])
                if match:
                    yield (Comment.Single, match.group(0))
                    pos += len(match.group(0))
                    continue
            
            # Strings
            if code[pos:pos+3] in ('"""', "'''"):
                quote = code[pos:pos+3]
                match = re.match(re.escape(quote) + r'.*?' + re.escape(quote), 
                               code[pos:], re.DOTALL)
                if match:
                    yield (String.Double, match.group(0))
                    pos += len(match.group(0))
                    continue
            
            if code[pos] in ('"', "'"):
                quote = code[pos]
                match = re.match(re.escape(quote) + r'(?:\\.|[^\\' + quote + r'])*' + re.escape(quote),
                               code[pos:])
                if match:
                    yield (String.Double, match.group(0))
                    pos += len(match.group(0))
                    continue
            
            # Numbers
            match = re.match(r'0[xX][0-9a-fA-F]+|0[oO][0-7]+|0[bB][01]+|'
                           r'\d+\.\d*|\.\d+|'
                           r'\d+[eE][+-]?\d+|\d+\.\d*[eE][+-]?\d+|'
                           r'\d+', code[pos:])
            if match:
                yield (Number.Integer, match.group(0))
                pos += len(match.group(0))
                continue
            
            # Identifiers and keywords
            match = re.match(r'[a-zA-Z_]\w*', code[pos:])
            if match:
                word = match.group(0)
                if word in self.KEYWORDS:
                    yield (Keyword, word)
                elif word in self.BUILTINS:
                    yield (Name.Builtin, word)
                else:
                    yield (Name, word)
                pos += len(word)
                continue
            
            # Operators
            match = re.match(r'(\*\*=|//=|<<=|>>=|&=|\|=|\^=|'
                           r'\+=|-=|\*=|/=|%=|@=|'
                           r'==|!=|<=|>=|<<|>>|'
                           r'\*\*|//|'
                           r'[+\-*/%@&|^~<>=!])', code[pos:])
            if match:
                yield (Operator, match.group(0))
                pos += len(match.group(0))
                continue
            
            # Punctuation
            if code[pos] in '()[]{}:;,.':
                yield (Punctuation, code[pos])
                pos += 1
                continue
            
            # Unknown character
            yield (Error, code[pos])
            pos += 1
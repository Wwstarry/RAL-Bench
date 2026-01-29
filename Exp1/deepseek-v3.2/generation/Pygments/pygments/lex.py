"""
Lexer interface and base classes.
"""

import re
from pygments.token import Token, _TokenType

class Lexer:
    """Base class for lexers."""
    
    def __init__(self, **options):
        self.options = options
        
    def get_tokens(self, text):
        """Return a generator of (token_type, value) pairs."""
        raise NotImplementedError
        
    def get_tokens_unprocessed(self, text):
        """Return a generator of (index, token_type, value) pairs."""
        for index, token, value in self.get_tokens(text):
            yield index, token, value

class RegexLexer(Lexer):
    """Lexer that uses regular expressions."""
    
    # Override in subclasses
    tokens = {}
    
    def get_tokens(self, text):
        pos = 0
        tokendefs = self.tokens.get('root', [])
        
        while pos < len(text):
            for rexmatch, action in tokendefs:
                m = rexmatch(text, pos)
                if m:
                    if isinstance(action, _TokenType):
                        yield action, m.group()
                    elif callable(action):
                        yield from action(self, m)
                    pos = m.end()
                    break
            else:
                # No match, advance by one character
                yield Token.Error, text[pos]
                pos += 1

def lex(code, lexer):
    """Lex the code with the given lexer and return token stream."""
    return lexer.get_tokens(code)
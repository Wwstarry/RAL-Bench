"""Lexer interface and base classes."""

import re
from pygments.token import Token

class Lexer:
    """Base class for lexers."""
    
    name = None
    aliases = []
    filenames = []
    mimetypes = []
    
    def __init__(self, **options):
        self.options = options
    
    def get_tokens(self, text):
        """Return a token stream from text."""
        return self.get_tokens_unprocessed(text)
    
    def get_tokens_unprocessed(self, text):
        """Return (index, token, value) tuples from text."""
        raise NotImplementedError


class RegexLexer(Lexer):
    """Lexer that uses regular expressions for tokenization."""
    
    # Token definitions as list of (pattern, token, state) tuples
    tokens = {}
    flags = 0
    
    def get_tokens_unprocessed(self, text):
        pos = 0
        statestack = ['root']
        statetokens = self.tokens
        regexes = {}
        
        # Compile regex patterns
        for state in statetokens:
            regexes[state] = []
            for pattern, token, new_state in statetokens[state]:
                if isinstance(token, str):
                    token = getattr(Token, token)
                regexes[state].append((re.compile(pattern, self.flags), token, new_state))
        
        while pos < len(text):
            current_state = statestack[-1]
            for regex, token, new_state in regexes[current_state]:
                match = regex.match(text, pos)
                if match:
                    value = match.group()
                    if token:
                        yield pos, token, value
                    pos = match.end()
                    
                    if new_state:
                        if new_state == '#pop':
                            statestack.pop()
                        elif new_state.startswith('#push:'):
                            statestack.append(new_state[6:])
                        else:
                            statestack.append(new_state)
                    break
            else:
                # No match found, advance by one character
                yield pos, Token.Error, text[pos]
                pos += 1
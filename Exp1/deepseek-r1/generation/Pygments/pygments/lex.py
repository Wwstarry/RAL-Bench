"""
Lexer interface and base classes.
"""

import re
from pygments.token import Token, _TokenType
from pygments.util import ClassNotFound, get_bool_opt, get_int_opt, get_list_opt

__all__ = ['Lexer', 'RegexLexer', 'lex']

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
    flags = 0
    
    def __init__(self, **options):
        super().__init__(**options)
        self._compile_rules()
        
    def _compile_rules(self):
        """Compile the regex patterns."""
        self._rules = []
        for state, rules in self.tokens.items():
            compiled = []
            for pattern, action in rules:
                if isinstance(action, _TokenType):
                    action = (action,)
                if isinstance(action, tuple):
                    action = (action[0], '')
                compiled.append((re.compile(pattern, self.flags), action))
            self._rules.append((state, compiled))
            
    def get_tokens(self, text):
        """Return tokens using regex matching."""
        pos = 0
        statestack = ['root']
        state = statestack[-1]
        
        while pos < len(text):
            for state, rules in self._rules:
                if state == statestack[-1]:
                    for regex, action in rules:
                        match = regex.match(text, pos)
                        if match:
                            value = match.group()
                            if isinstance(action, _TokenType):
                                yield action, value
                            elif isinstance(action, tuple):
                                if len(action) == 2:
                                    yield action[0], value
                                    if action[1]:
                                        if action[1].startswith('#'):
                                            statestack.append(action[1][1:])
                                        elif action[1] == '#pop':
                                            statestack.pop()
                                        elif action[1].startswith('#push:'):
                                            statestack.append(action[1][6:])
                            pos = match.end()
                            break
                    else:
                        # No match
                        yield Token.Error, text[pos]
                        pos += 1
                    break
            else:
                # No state found
                yield Token.Error, text[pos]
                pos += 1
                
        # End of text
        yield Token.Text, ''

def lex(code, lexer):
    """Lex code with given lexer and return token stream."""
    return lexer.get_tokens(code)
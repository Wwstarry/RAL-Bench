import re
from pygments.token import Token, Text, Whitespace, Comment, Keyword, Name, String, Number, Operator, Punctuation, Error

def lex(code, lexer):
    """
    Lex the code using the given lexer instance.
    Returns an iterable of (token_type, text) tuples.
    """
    return lexer.get_tokens(code)

class RegexLexer:
    """
    Base class for regex-based lexers.
    Subclasses should define a 'tokens' dict mapping state names to lists of
    (regex, action) tuples.
    """
    tokens = {}

    def __init__(self, **options):
        self.options = options
        self._statestack = ['root']

    def get_tokens_unprocessed(self, text):
        pos = 0
        statestack = self._statestack[:]
        while pos < len(text):
            state = statestack[-1]
            for regex, action in self.tokens[state]:
                m = regex.match(text, pos)
                if m:
                    if callable(action):
                        for item in action(self, m):
                            yield item
                    elif isinstance(action, str):
                        # push state
                        statestack.append(action)
                    elif isinstance(action, tuple):
                        # (token, nextstate)
                        token, nextstate = action
                        yield token, m.group()
                        if nextstate == '#pop':
                            statestack.pop()
                        elif nextstate == '#push':
                            statestack.append(state)
                        elif nextstate is not None:
                            statestack.append(nextstate)
                    else:
                        # token only
                        yield action, m.group()
                    pos = m.end()
                    break
            else:
                # No rule matched
                yield Error, text[pos]
                pos += 1

    def get_tokens(self, text):
        for ttype, value in self.get_tokens_unprocessed(text):
            yield ttype, value
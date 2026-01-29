"""
Lexing functions and base classes.
"""

import re
from pygments.token import Token, Text, Error


def lex(code, lexer):
    """
    Lex code with the given lexer.
    
    Args:
        code: Source code string
        lexer: Lexer instance
        
    Yields:
        (tokentype, value) tuples
    """
    return lexer.get_tokens(code)


class Lexer:
    """
    Base class for all lexers.
    """
    
    name = None
    aliases = []
    filenames = []
    mimetypes = []
    
    def __init__(self, **options):
        self.options = options
        self.stripnl = options.get('stripnl', True)
        self.stripall = options.get('stripall', False)
        self.ensurenl = options.get('ensurenl', True)
        self.tabsize = options.get('tabsize', 0)
        self.encoding = options.get('encoding', 'utf-8')
    
    def get_tokens(self, text, unfiltered=False):
        """
        Return an iterator of (tokentype, value) tuples.
        """
        if isinstance(text, bytes):
            text = text.decode(self.encoding)
        
        if self.stripall:
            text = text.strip()
        elif self.stripnl:
            text = text.rstrip('\n')
        
        if self.ensurenl and text and not text.endswith('\n'):
            text += '\n'
        
        if self.tabsize > 0:
            text = text.expandtabs(self.tabsize)
        
        return self.get_tokens_unprocessed(text)
    
    def get_tokens_unprocessed(self, text):
        """
        Return an iterator of (index, tokentype, value) tuples.
        Subclasses should override this method.
        """
        yield 0, Text, text
    
    def analyse_text(text):
        """
        Return a float between 0 and 1 indicating how likely it is
        that the text is in this language.
        """
        return 0.0


class RegexLexer(Lexer):
    """
    Base class for lexers using regular expressions.
    """
    
    flags = re.MULTILINE
    tokens = {}
    
    def get_tokens_unprocessed(self, text):
        """
        Split text into tokens using regular expressions.
        """
        pos = 0
        stack = ['root']
        statetokens = self.tokens.get('root', [])
        
        while pos < len(text):
            for rexmatch, action, new_state in statetokens:
                m = rexmatch.match(text, pos)
                if m:
                    if isinstance(action, type) and issubclass(action, Token.__class__):
                        yield pos, action, m.group()
                    elif callable(action):
                        for item in action(self, m):
                            if len(item) == 2:
                                yield pos, item[0], item[1]
                            else:
                                yield item
                    else:
                        yield pos, action, m.group()
                    
                    pos = m.end()
                    
                    if new_state is not None:
                        if isinstance(new_state, str):
                            stack.append(new_state)
                            statetokens = self.tokens.get(new_state, [])
                        elif new_state == '#pop':
                            if len(stack) > 1:
                                stack.pop()
                                statetokens = self.tokens.get(stack[-1], [])
                        elif new_state == '#push':
                            stack.append(stack[-1])
                        elif isinstance(new_state, tuple):
                            for state in new_state:
                                if state == '#pop':
                                    if len(stack) > 1:
                                        stack.pop()
                                elif state == '#push':
                                    stack.append(stack[-1])
                                else:
                                    stack.append(state)
                            statetokens = self.tokens.get(stack[-1], [])
                    break
            else:
                # No match found, emit error token and advance
                yield pos, Error, text[pos]
                pos += 1


def bygroups(*args):
    """
    Callback that yields multiple tokens for groups in the match.
    """
    def callback(lexer, match):
        for i, token in enumerate(args, 1):
            text = match.group(i)
            if text:
                yield token, text
    return callback


def using(lexer_cls, **options):
    """
    Callback that lexes the match with a different lexer.
    """
    def callback(lexer, match):
        sublexer = lexer_cls(**options)
        for item in sublexer.get_tokens_unprocessed(match.group()):
            yield item
    return callback


def include(state):
    """
    Include rules from another state.
    """
    return ('__include__', state)


def default(state):
    """
    Jump to another state on no match.
    """
    return ('__default__', state)
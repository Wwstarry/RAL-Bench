# -*- coding: utf-8 -*-
"""
    pygments.lex
    ~~~~~~~~~~~

    Lexer interface and basic lexer implementations.

    :copyright: Copyright 2006-2023 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re

from pygments.token import Error, Text, Other
from pygments.util import get_bool_opt


class LexerMeta(type):
    """
    This metaclass automagically converts ``tokens`` dictionaries in
    class attributes into the correct data structures.
    """

    def __new__(mcs, name, bases, d):
        tokens = {}
        for b in bases:
            if hasattr(b, 'tokens'):
                tokens.update(b.tokens)
        if 'tokens' in d:
            tokens.update(d.pop('tokens'))
        d['tokens'] = tokens
        return type.__new__(mcs, name, bases, d)


class Lexer(metaclass=LexerMeta):
    """
    Base class for all lexers.
    """
    name = None
    aliases = []
    filenames = []
    mimetypes = []

    def __init__(self, **options):
        self.options = options
        self.stripnl = get_bool_opt(options, 'stripnl', True)
        self.stripall = get_bool_opt(options, 'stripall', False)

    def analyse_text(text):
        """
        Return a float between 0 and 1 indicating the likelihood that
        this lexer is appropriate for the given text.

        The default implementation simply returns 0.0.
        """
        return 0.0

    def get_tokens(self, text):
        """
        Return an iterable of (tokentype, value) pairs generated from
        `text`.
        """
        raise NotImplementedError

    def get_tokens_unprocessed(self, text):
        """
        Return an iterable of (index, tokentype, value) pairs where index is the
        starting position of the token.
        """
        raise NotImplementedError


class RegexLexer(Lexer):
    """
    Base class for simple stateful regular expression-based lexers.
    Subclasses must define ``tokens`` as a dictionary of state names to
    lists of regular expression rules.
    """
    def __init__(self, **options):
        Lexer.__init__(self, **options)
        self._tokens = {}
        for state, state_rules in self.tokens.items():
            rules = []
            for rule in state_rules:
                if len(rule) == 2:
                    regex, token = rule
                    action = None
                else:
                    regex, token, action = rule
                rules.append((re.compile(regex, re.UNICODE | re.MULTILINE), token, action))
            self._tokens[state] = rules

    def get_tokens_unprocessed(self, text):
        """
        Tokenize a string and return an iterator of (index, tokentype, value) tuples.
        """
        pos = 0
        statestack = ['root']
        statetokens = self._tokens['root']
        
        while pos < len(text):
            for regex, token, action in statetokens:
                match = regex.match(text, pos)
                if match:
                    if token:
                        yield pos, token, match.group()
                    pos = match.end()
                    if action:
                        if isinstance(action, str):
                            if action.startswith('#pop'):
                                for _ in range(action.count('#pop')):
                                    if len(statestack) > 1:
                                        statestack.pop()
                                if action.startswith('#pop#push'):
                                    statestack.append(action[9:])
                            elif action == '#push':
                                statestack.append(statestack[-1])
                            else:
                                statestack.append(action)
                            statetokens = self._tokens[statestack[-1]]
                        else:
                            # Assume it's a callable
                            action(match)
                    break
            else:
                # No match, output one character as error and continue
                yield pos, Error, text[pos]
                pos += 1

    def get_tokens(self, text):
        """
        Return an iterable of (tokentype, value) pairs generated from
        `text`.
        """
        for i, t, v in self.get_tokens_unprocessed(text):
            yield t, v
"""
    pygments.lexers
    ~~~~~~~~~~~~~~~

    Pygments lexers.

    :copyright: Copyright 2006-2021 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re
from collections import deque

from pygments.token import Error, Text
from pygments.util import ClassNotFound, docstring_headline

__all__ = ['get_lexer_by_name', 'guess_lexer', 'Lexer', 'RegexLexer']

_LEXERS = {}

def _import_lexers():
    """Dynamically import all lexers."""
    from . import python, json, ini
    for lexer_cls in [python.PythonLexer, json.JsonLexer, ini.IniLexer]:
        for alias in lexer_cls.aliases:
            _LEXERS[alias] = lexer_cls
_import_lexers()


def get_lexer_by_name(alias, **options):
    """
    Get a lexer by an alias.
    Raises ClassNotFound if no lexer is found.
    """
    if alias.lower() in _LEXERS:
        return _LEXERS[alias.lower()](**options)
    raise ClassNotFound(f"No lexer for alias '{alias}' found")


class Lexer:
    """
    Base for all lexers.
    """
    name = None
    aliases = []
    filenames = []
    mimetypes = []

    def __init__(self, **options):
        self.options = options

    def get_tokens(self, text, unfiltered=False):
        """
        Return an iterable of (tokentype, value) pairs.
        """
        # In this implementation, we don't support filters,
        # so `unfiltered` is ignored.
        return self.get_tokens_unprocessed(text)

    def get_tokens_unprocessed(self, text):
        """
        This method should be overridden by subclasses to provide the
        token stream.
        """
        raise NotImplementedError


class RegexLexer(Lexer):
    """
    A lexer that uses regular expressions to tokenize text.
    Subclasses must define a `tokens` dictionary that maps state names
    to a list of rules.
    """
    flags = re.MULTILINE

    def get_tokens_unprocessed(self, text, stack=('root',)):
        """
        Split `text` into tokens.
        `stack` is the initial state stack.
        """
        tokendefs = self.tokens
        statestack = list(stack)
        statetokens = tokendefs[statestack[-1]]
        pos = 0
        text_len = len(text)

        while pos < text_len:
            for rex, action, new_state in statetokens:
                m = rex.match(text, pos)
                if m:
                    if callable(action):
                        yield from action(self, m)
                    elif isinstance(action, tuple):
                        for item in action:
                            yield item
                    else:
                        yield action, m.group()

                    if new_state is not None:
                        if isinstance(new_state, str):
                            if new_state == '#pop':
                                statestack.pop()
                            elif new_state == '#push':
                                statestack.append(statestack[-1])
                            else:
                                statestack[-1] = new_state
                        elif isinstance(new_state, int):
                            if new_state == -1:
                                statestack.pop()
                            else:
                                for _ in range(new_state):
                                    statestack.pop()
                        elif isinstance(new_state, tuple):
                            for state in new_state:
                                if state == '#pop':
                                    statestack.pop()
                                elif state == '#push':
                                    statestack.append(statestack[-1])
                                else:
                                    statestack.append(state)
                        else: # Should be a state name
                            statestack.append(new_state)

                    pos = m.end()
                    statetokens = tokendefs[statestack[-1]]
                    break
            else:
                # no match
                yield Error, text[pos]
                pos += 1
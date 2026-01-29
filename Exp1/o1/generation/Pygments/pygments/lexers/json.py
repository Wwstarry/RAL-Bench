"""
A minimal JSON lexer.
"""

import re

from ..token import Text, String, Number, Keyword, Punctuation, Operator, Token
from ..util import option

class JsonLexer:
    name = "JSON"

    # Simple patterns
    token_pattern = re.compile(
        r'''(?P<whitespace>\s+)
         |(?P<string>"[^"\\]*(?:\\.[^"\\]*)*")
         |(?P<number>-?\d+(\.\d+)?([eE][+\-]?\d+)?)
         |(?P<true>\btrue\b)
         |(?P<false>\bfalse\b)
         |(?P<null>\bnull\b)
         |(?P<punctuation>[{}\[\],:])
         ''',
        re.MULTILINE | re.VERBOSE
    )

    def __init__(self, **options):
        pass

    def get_tokens(self, text, **options):
        pos = 0
        length = len(text)

        while True:
            if pos >= length:
                break
            match = self.token_pattern.search(text, pos)
            if not match:
                # yield the rest as Text
                yield Text, text[pos:]
                break

            start = match.start()
            if start > pos:
                yield Text, text[pos:start]

            groupname = match.lastgroup
            value = match.group(groupname)
            pos = match.end()

            if groupname == 'whitespace':
                yield Text, value
            elif groupname == 'string':
                yield String, value
            elif groupname == 'number':
                yield Number, value
            elif groupname == 'true':
                yield Keyword, value
            elif groupname == 'false':
                yield Keyword, value
            elif groupname == 'null':
                yield Keyword, value
            elif groupname == 'punctuation':
                yield Punctuation, value
            else:
                yield Text, value
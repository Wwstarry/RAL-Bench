"""
A minimal Python lexer.
"""

import re

from ..token import Text, Keyword, Name, Comment, String, Number, Operator, Punctuation, Token
from ..util import option

class PythonLexer:
    name = "Python"

    # Very simplified sets of tokens
    _keywords = {
        "def", "class", "if", "elif", "else", "for", "while", "try",
        "except", "finally", "return", "import", "from", "as", "pass",
        "break", "continue", "lambda", "with", "yield", "in", "is",
        "and", "or", "not", "global", "assert", "del", "raise"
    }

    _builtins = {
        "print", "range", "len", "dict", "list", "set", "tuple", "str",
        "int", "float", "bool", "True", "False", "None"
    }

    token_pattern = re.compile(
        r'''(?P<whitespace>\s+)
         |(?P<number>\b\d+(\.\d+)?\b)
         |(?P<string>'[^'\\]*(?:\\.[^'\\]*)*'|"[^"\\]*(?:\\.[^"\\]*)*")
         |(?P<identifier>[A-Za-z_]\w*)
         |(?P<comment>#.*?$)
         |(?P<operator>[+\-*/%//=]=?|==|!=|<=|>=|<>|\*\*|\+=|-=|\*=|/=|//|%)
         |(?P<punctuation>[\(\)\[\]\{\}:,.;])
         ''',
        re.MULTILINE | re.VERBOSE
    )

    def __init__(self, **options):
        pass

    def get_tokens(self, text, **options):
        pos = 0
        length = len(text)

        for match in self.token_pattern.finditer(text):
            start = match.start()
            if start > pos:
                # yield any text between matches
                yield Text, text[pos:start]
            pos = match.end()

            groupname = match.lastgroup
            value = match.group(groupname)
            if groupname == 'whitespace':
                yield Text, value
            elif groupname == 'number':
                yield Number, value
            elif groupname == 'string':
                yield String, value
            elif groupname == 'identifier':
                if value in self._keywords:
                    yield Keyword, value
                elif value in self._builtins:
                    yield Name.Builtin, value
                else:
                    yield Name, value
            elif groupname == 'comment':
                yield Comment, value
            elif groupname == 'operator':
                yield Operator, value
            elif groupname == 'punctuation':
                yield Punctuation, value
            else:
                yield Text, value

        if pos < length:
            # leftover text
            yield Text, text[pos:]
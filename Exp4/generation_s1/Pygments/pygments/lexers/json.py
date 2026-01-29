from __future__ import annotations

import re
from typing import Iterable, Tuple

from pygments.lex import Lexer
from pygments.token import Error, Keyword, Literal, Number, Punctuation, Text, TokenType, Whitespace

_ws_re = re.compile(r"[ \t\f\v]+")
_nl_re = re.compile(r"\r\n|\r|\n")
_str_re = re.compile(r'"(?:\\["\\/bfnrt]|\\u[0-9a-fA-F]{4}|[^"\\])*"')
_num_re = re.compile(r"-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?")
_const_re = re.compile(r"(true|false|null)\b")
_punct_re = re.compile(r"[{}\[\],:]")

class JsonLexer(Lexer):
    name = "JSON"
    aliases = ["json"]
    filenames = ["*.json"]
    mimetypes = ["application/json"]

    def get_tokens(self, text: str) -> Iterable[Tuple[TokenType, str]]:
        i, n = 0, len(text)
        while i < n:
            m = _ws_re.match(text, i)
            if m:
                yield Whitespace, m.group(0)
                i = m.end()
                continue
            m = _nl_re.match(text, i)
            if m:
                yield Text, m.group(0)
                i = m.end()
                continue
            m = _str_re.match(text, i)
            if m:
                yield Literal.String.Double, m.group(0)
                i = m.end()
                continue
            m = _num_re.match(text, i)
            if m:
                yield Number, m.group(0)
                i = m.end()
                continue
            m = _const_re.match(text, i)
            if m:
                yield Keyword.Constant, m.group(1)
                i = m.end()
                continue
            m = _punct_re.match(text, i)
            if m:
                yield Punctuation, m.group(0)
                i = m.end()
                continue
            # fallback
            yield Error, text[i]
            i += 1
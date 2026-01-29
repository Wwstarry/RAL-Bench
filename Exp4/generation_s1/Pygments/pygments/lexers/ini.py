from __future__ import annotations

import re
from typing import Iterable, Tuple

from pygments.lex import Lexer
from pygments.token import Comment, Literal, Name, Operator, Punctuation, Text, TokenType, Whitespace

_ws_re = re.compile(r"[ \t\f\v]+")
_nl_re = re.compile(r"\r\n|\r|\n")
_comment_re = re.compile(r"[;#][^\r\n]*")

_section_re = re.compile(r"\[([^\]\r\n]+)\]")

class IniLexer(Lexer):
    name = "INI"
    aliases = ["ini", "cfg", "dosini"]
    filenames = ["*.ini", "*.cfg"]
    mimetypes = ["text/plain"]

    def get_tokens(self, text: str) -> Iterable[Tuple[TokenType, str]]:
        i, n = 0, len(text)
        bol = True  # beginning of line

        while i < n:
            m = _nl_re.match(text, i)
            if m:
                yield Text, m.group(0)
                i = m.end()
                bol = True
                continue

            m = _ws_re.match(text, i)
            if m:
                yield Whitespace, m.group(0)
                i = m.end()
                continue

            m = _comment_re.match(text, i)
            if m:
                yield Comment.Single, m.group(0)
                i = m.end()
                bol = False
                continue

            if bol:
                m = _section_re.match(text, i)
                if m:
                    sec = m.group(1)
                    yield Punctuation, "["
                    yield Name.Namespace, sec
                    yield Punctuation, "]"
                    i = m.end()
                    bol = False
                    continue

                # key parsing at BOL: read until '=' or ':' or newline
                j = i
                while j < n and text[j] not in "\r\n=:":
                    # stop before inline comment if it starts at key area? keep simple: allow
                    j += 1
                # if we hit separator
                if j < n and text[j] in "=:":
                    key = text[i:j].rstrip()
                    if key:
                        # emit key and preserve any trailing spaces between key and sep
                        klen = len(key)
                        yield Name.Attribute, text[i : i + klen]
                        rest = text[i + klen : j]
                        if rest:
                            yield Whitespace, rest
                    else:
                        # no key content, just fall through
                        pass
                    sep = text[j]
                    yield Operator, sep
                    i = j + 1
                    bol = False
                    continue

            # value / general text until newline or comment start
            if text[i] in "=:":  # stray separators
                yield Operator, text[i]
                i += 1
                bol = False
                continue

            # if we see a comment start mid-line, treat as comment
            m = _comment_re.match(text, i)
            if m:
                yield Comment.Single, m.group(0)
                i = m.end()
                bol = False
                continue

            # default: consume one char as value-ish
            yield Literal.String, text[i]
            i += 1
            bol = False
from __future__ import annotations

import re
from typing import Iterable, Iterator, List, Tuple

from pygments.lex import Lexer
from pygments.token import (
    Comment,
    Error,
    Keyword,
    Literal,
    Name,
    Number,
    Operator,
    Punctuation,
    Text,
    TokenType,
    Whitespace,
)

_PY_KEYWORDS = {
    "def",
    "class",
    "if",
    "elif",
    "else",
    "for",
    "while",
    "return",
    "import",
    "from",
    "as",
    "try",
    "except",
    "finally",
    "with",
    "lambda",
    "yield",
    "pass",
    "break",
    "continue",
    "in",
    "is",
    "and",
    "or",
    "not",
    "raise",
    "del",
    "global",
    "nonlocal",
    "assert",
}
_PY_CONSTANTS = {"True", "False", "None"}

_ident = r"[A-Za-z_][A-Za-z0-9_]*"

# Order matters.
_ws_re = re.compile(r"[ \t\f\v]+")
_nl_re = re.compile(r"\r\n|\r|\n")
_comment_re = re.compile(r"#[^\r\n]*")
_triple_re = re.compile(r"(?s)(?:'''|\"\"\").*?(?:'''|\"\"\")")
# strings: simplistic but good enough for tests
_sq_re = re.compile(r"(?s)'(?:\\.|[^'\\])*'")
_dq_re = re.compile(r'(?s)"(?:\\.|[^"\\])*"')
_num_re = re.compile(r"(?:\d+\.\d*|\d*\.\d+|\d+)(?:[eE][+-]?\d+)?")
_decorator_re = re.compile(rf"@({_ident})(?:\.{_ident})*")
_ident_re = re.compile(_ident)
_op_re = re.compile(r"(==|!=|<=|>=|<<|>>|\*\*|//|->|:=|[+\-*/%&|^~<>]=?|=)")
_punct_re = re.compile(r"[\[\]{}().,:;]")

# For def/class name capture: handled by a small state machine.
_defclass_re = re.compile(rf"(def|class)\b")


class PythonLexer(Lexer):
    name = "Python"
    aliases = ["python", "py"]
    filenames = ["*.py"]
    mimetypes = ["text/x-python"]

    def get_tokens(self, text: str) -> Iterable[Tuple[TokenType, str]]:
        i = 0
        n = len(text)
        expect_name: str | None = None  # "def" or "class"

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
                expect_name = None
                continue

            m = _comment_re.match(text, i)
            if m:
                yield Comment.Single, m.group(0)
                i = m.end()
                continue

            m = _triple_re.match(text, i)
            if m:
                yield Literal.String.Doc, m.group(0)
                i = m.end()
                continue

            m = _sq_re.match(text, i)
            if m:
                yield Literal.String.Single, m.group(0)
                i = m.end()
                continue

            m = _dq_re.match(text, i)
            if m:
                yield Literal.String.Double, m.group(0)
                i = m.end()
                continue

            m = _decorator_re.match(text, i)
            if m:
                # '@' punctuation then decorator name
                deco = m.group(0)
                yield Punctuation, "@"
                yield Name.Decorator, deco[1:]
                i = m.end()
                continue

            m = _num_re.match(text, i)
            if m:
                s = m.group(0)
                if "." in s or "e" in s.lower():
                    yield Number.Float, s
                else:
                    yield Number.Integer, s
                i = m.end()
                continue

            m = _defclass_re.match(text, i)
            if m:
                kw = m.group(1)
                yield Keyword, kw
                i = m.end()
                expect_name = kw
                continue

            m = _ident_re.match(text, i)
            if m:
                ident = m.group(0)
                if ident in _PY_CONSTANTS:
                    yield Keyword.Constant, ident
                elif ident in _PY_KEYWORDS:
                    # treat "and/or/not/in/is" as Operator.Word in real pygments; keep Keyword for simplicity
                    yield Keyword, ident
                else:
                    if expect_name == "def":
                        yield Name.Function, ident
                        expect_name = None
                    elif expect_name == "class":
                        yield Name.Class, ident
                        expect_name = None
                    else:
                        yield Name, ident
                i = m.end()
                continue

            m = _op_re.match(text, i)
            if m:
                yield Operator, m.group(0)
                i = m.end()
                continue

            m = _punct_re.match(text, i)
            if m:
                yield Punctuation, m.group(0)
                i = m.end()
                continue

            # fallback: consume one char
            ch = text[i]
            # mark obviously weird control characters as Error; else Text
            if ch and ord(ch) < 32 and ch not in ("\t", "\n", "\r"):
                yield Error, ch
            else:
                yield Text, ch
            i += 1
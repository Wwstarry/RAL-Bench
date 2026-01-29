"""
Registration hub for the bundled subset of lexers.
"""

from __future__ import annotations

import re
import tokenize
from io import BytesIO
from keyword import kwlist as _py_keywords
from typing import Dict, Iterable, List, Tuple

from pygments.token import Token
from pygments.util import ClassNotFound

TokenStream = Iterable[Tuple[Token, str]]

__all__ = [
    "BaseLexer",
    "PythonLexer",
    "JsonLexer",
    "IniLexer",
    "get_lexer_by_name",
]

###############################################################################
# Base class
###############################################################################


class BaseLexer:
    """
    Minimal common interface for lexers.
    """

    name: str = "text"
    aliases: List[str] = []
    filenames: List[str] = []

    def get_tokens(self, text: str) -> TokenStream:
        """
        Subclasses must implement this to yield ``(tokentype, value)`` tuples.
        """
        raise NotImplementedError


###############################################################################
# Helper: simple registry
###############################################################################

_LEXER_REGISTRY: Dict[str, "BaseLexer"] = {}


def _register(lexer_cls):
    instance = lexer_cls()
    for alias in lexer_cls.aliases:
        _LEXER_REGISTRY[alias.lower()] = instance
    _LEXER_REGISTRY[lexer_cls.name.lower()] = instance
    return lexer_cls


def get_lexer_by_name(name: str) -> BaseLexer:
    """
    Return a lexer *instance* given its short name.
    """
    try:
        return _LEXER_REGISTRY[name.lower()]
    except KeyError as exc:  # pragma: no cover
        raise ClassNotFound(f"no lexer for alias {name!r}") from exc


###############################################################################
# Python lexer (very thin wrapper around stdlib `tokenize`)
###############################################################################


@_register
class PythonLexer(BaseLexer):
    name = "python"
    aliases = ["python", "py"]

    def get_tokens(self, text: str) -> TokenStream:
        if not text.endswith("\n"):
            text += "\n"
        try:
            tokens = tokenize.tokenize(BytesIO(text.encode()).readline)
        except Exception:
            yield Token.Error, text
            return

        for tok_type, tok_str, _start, _end, _line in tokens:
            if tok_type == tokenize.ENDMARKER:
                break
            if tok_type == tokenize.NEWLINE or tok_type == tokenize.NL:
                yield Token.Text, tok_str
            elif tok_type == tokenize.COMMENT:
                yield Token.Comment.Single, tok_str
            elif tok_type == tokenize.STRING:
                yield Token.Literal.String, tok_str
            elif tok_type == tokenize.NUMBER:
                yield Token.Number, tok_str
            elif tok_type == tokenize.OP:
                yield Token.Operator, tok_str
            elif tok_type == tokenize.NAME:
                if tok_str in _py_keywords:
                    yield Token.Keyword, tok_str
                else:
                    yield Token.Name, tok_str
            else:
                # whitespace etc.
                yield Token.Text, tok_str


###############################################################################
# JSON lexer (very rough)
###############################################################################


@_register
class JsonLexer(BaseLexer):
    name = "json"
    aliases = ["json"]

    _whitespace_re = re.compile(r"\s+")
    _number_re = re.compile(r"-?(0|[1-9]\d*)(\.\d+)?([eE][+-]?\d+)?")
    _string_re = re.compile(
        r'"(\\\\|\\"|[^"])*"'  # simplistic string pattern
    )

    _keywords = {"true", "false", "null"}

    def get_tokens(self, text: str) -> TokenStream:
        i = 0
        n = len(text)
        while i < n:
            # Whitespace
            m = self._whitespace_re.match(text, i)
            if m:
                yield Token.Text, m.group(0)
                i = m.end()
                continue

            # String
            m = self._string_re.match(text, i)
            if m:
                yield Token.Literal.String.Double, m.group(0)
                i = m.end()
                continue

            # Number
            m = self._number_re.match(text, i)
            if m:
                yield Token.Number, m.group(0)
                i = m.end()
                continue

            # Punctuation
            ch = text[i]
            if ch in "{}[]:,":
                yield Token.Punctuation, ch
                i += 1
                continue

            # Words / keywords (unlikely in valid json but still)
            if ch.isalpha():
                j = i + 1
                while j < n and text[j].isalpha():
                    j += 1
                word = text[i:j]
                if word in self._keywords:
                    yield Token.Keyword.Constant, word
                else:
                    yield Token.Name, word
                i = j
                continue

            # Fallback
            yield Token.Error, ch
            i += 1


###############################################################################
# INI lexer (very small)
###############################################################################


@_register
class IniLexer(BaseLexer):
    name = "ini"
    aliases = ["ini", "cfg"]

    _section_re = re.compile(r"\[\s*([^\]]+?)\s*]")

    def get_tokens(self, text: str) -> TokenStream:
        for line in text.splitlines(keepends=True):
            m = self._section_re.match(line)
            if m:
                yield Token.Name.Class, line.rstrip("\n")
                yield Token.Text, "\n"
                continue

            if not line.strip() or line.lstrip().startswith(("#", ";")):
                # Comment / empty
                yield Token.Comment.Single, line
                continue

            # key = value
            if "=" in line:
                key, value = line.split("=", 1)
                yield Token.Name, key.rstrip()
                yield Token.Operator, "="
                yield Token.Literal.String, value.lstrip()
            else:
                yield Token.Text, line


# The module is imported by pygments.__init__, so registry is now populated.
from __future__ import annotations

from typing import Dict, Iterable, Optional, Tuple

from pygments.token import Comment, Keyword, Literal, Name, Number, Text, Token, TokenType
from pygments.util import get_bool_opt


_RESET = "\x1b[0m"

# Simple, deterministic mapping.
# Use fairly standard colors that shouldn't vary.
_SGR = {
    "comment": "\x1b[90m",   # bright black
    "keyword": "\x1b[94m",   # bright blue
    "namefunc": "\x1b[92m",  # bright green
    "nameclass": "\x1b[96m", # bright cyan
    "string": "\x1b[93m",    # bright yellow
    "number": "\x1b[95m",    # bright magenta
}


class TerminalFormatter:
    name = "Terminal"
    aliases = ["terminal", "ansi"]

    def __init__(self, **options):
        self.options = dict(options)
        self.ansi = get_bool_opt(options, "ansi", True)
        self.stripnl = get_bool_opt(options, "stripnl", False)

    def _style_for(self, ttype: TokenType) -> str:
        if ttype in Comment:
            return _SGR["comment"]
        if ttype in Keyword:
            return _SGR["keyword"]
        if ttype in Name.Function:
            return _SGR["namefunc"]
        if ttype in Name.Class:
            return _SGR["nameclass"]
        if ttype in Literal.String:
            return _SGR["string"]
        if ttype in Number:
            return _SGR["number"]
        return ""

    def format(self, tokensource: Iterable[Tuple[TokenType, str]], outfile) -> Optional[str]:
        if not self.ansi:
            for _, value in tokensource:
                if self.stripnl:
                    value = value.replace("\n", "")
                outfile.write(value)
            return None

        cur = ""
        for ttype, value in tokensource:
            if self.stripnl:
                value = value.replace("\n", "")
            style = self._style_for(ttype)
            if style != cur:
                if cur:
                    outfile.write(_RESET)
                if style:
                    outfile.write(style)
                cur = style
            outfile.write(value)
        if cur:
            outfile.write(_RESET)
        return None
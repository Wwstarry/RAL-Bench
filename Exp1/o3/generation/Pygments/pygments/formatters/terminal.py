"""
Very small ANSI / terminal formatter.
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Tuple

from pygments.token import Token, is_token_subtype

TokenStream = Iterable[Tuple[Token, str]]


class TerminalFormatter:
    """
    Emits ANSI colored output (foreground only).
    """

    _ANSI_RESET = "\x1b[39;49;00m"

    _token_colors: Dict[Token, str] = {
        Token.Keyword: "\x1b[34m",  # blue
        Token.Comment: "\x1b[90m",  # bright black
        Token.String: "\x1b[32m",  # green
        Token.Number: "\x1b[36m",  # cyan
        Token.Operator: "\x1b[35m",  # magenta
        Token.Name.Function: "\x1b[33m",  # yellow
        Token.Name.Class: "\x1b[33m",  # yellow
    }

    def __init__(self, colors: bool = True):
        self.colors = colors

    # ------------------------------------------------------------------ #

    def format(self, tokensource: TokenStream, outfile):
        for ttype, value in tokensource:
            if self.colors:
                color = self._lookup_color(ttype)
                if color:
                    outfile.write(color + value + self._ANSI_RESET)
                else:
                    outfile.write(value)
            else:
                outfile.write(value)

    def _lookup_color(self, token: Token) -> str:
        while token:
            if token in self._token_colors:
                return self._token_colors[token]
            token = token[:-1]  # type: ignore
        return ""


__all__: List[str] = ["TerminalFormatter"]
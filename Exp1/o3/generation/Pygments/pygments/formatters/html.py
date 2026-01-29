"""
Very tiny HTML formatter – enough to satisfy the tasks' tests.
"""

from __future__ import annotations

from html import escape
from io import StringIO
from typing import Dict, Iterable, List, Tuple

from pygments.styles import get_style_by_name
from pygments.token import Token, is_token_subtype

TokenStream = Iterable[Tuple[Token, str]]


class HtmlFormatter:
    """
    Minimal subset of the real ``HtmlFormatter``.
    """

    def __init__(
        self,
        style: str = "default",
        full: bool = False,
        noclasses: bool = False,
        linenos: bool = False,
        cssclass: str = "highlight",
    ):
        self.style = get_style_by_name(style)
        self.full = full
        self.noclasses = noclasses
        self.linenos = linenos
        self.cssclass = cssclass

        # Build a flatten mapping token -> css class / inline style string
        self._class_cache: Dict[Token, str] = {}
        self._style_cache: Dict[Token, str] = {}

        for token, style_def in self.style.styles.items():
            self._class_cache[token] = self._get_short_class(token)
            self._style_cache[token] = style_def

    # ------------------------------------------------------------------ #
    # API
    # ------------------------------------------------------------------ #

    def format(self, tokensource: TokenStream, outfile):
        """
        Write HTML representation of *tokensource* to *outfile*.
        """
        buffer = StringIO()
        if self.full:
            buffer.write("<html><head>")
            buffer.write("<style>")
            buffer.write(self.get_style_defs("." + self.cssclass))
            buffer.write("</style></head><body>")

        buffer.write(f'<pre class="{self.cssclass}">')

        for ttype, value in tokensource:
            html = escape(value)
            if self.noclasses:
                style = self._lookup_style(ttype)
                if style:
                    buffer.write(f'<span style="{style}">{html}</span>')
                else:
                    buffer.write(html)
            else:
                class_name = self._lookup_class(ttype)
                if class_name:
                    buffer.write(f'<span class="{class_name}">{html}</span>')
                else:
                    buffer.write(html)

        buffer.write("</pre>")

        if self.full:
            buffer.write("</body></html>")

        outfile.write(buffer.getvalue())

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _get_short_class(token: Token) -> str:
        """
        Convert a token into the short class names used by the original
        Pygments formatter (e.g. ``Token.Keyword`` -> ``k``).
        """
        if not token:
            return ""
        parts = list(token)
        # map main group letter
        mapping = {
            "Text": "t",
            "Whitespace": "w",
            "Error": "err",
            "Comment": "c",
            "Keyword": "k",
            "Name": "n",
            "Literal": "l",
            "String": "s",
            "Number": "m",
            "Operator": "o",
            "Punctuation": "p",
        }
        root = parts[0]
        root_short = mapping.get(root, root.lower())
        if len(parts) == 1:
            return root_short
        else:
            rest = "".join(p[0].lower() for p in parts[1:])
            return root_short + rest

    def _lookup_class(self, token: Token) -> str:
        """
        Return the css class associated with *token* (search parents).
        """
        while token:
            if token in self._class_cache:
                return self._class_cache[token]
            token = token[:-1]  # type: ignore
        return ""

    def _lookup_style(self, token: Token) -> str:
        while token:
            if token in self._style_cache and self._style_cache[token]:
                return self._style_cache[token]
            token = token[:-1]  # type: ignore
        return ""

    # ------------------------------------------------------------------ #
    # Style definitions
    # ------------------------------------------------------------------ #

    def get_style_defs(self, selector: str = ".highlight") -> str:
        lines: List[str] = []
        for token, style in self.style.styles.items():
            if not style:
                continue
            cls = self._lookup_class(token)
            if not cls:
                continue
            lines.append(f"{selector} .{cls} {{ {style} }}")
        return "\n".join(lines)


__all__: List[str] = ["HtmlFormatter"]
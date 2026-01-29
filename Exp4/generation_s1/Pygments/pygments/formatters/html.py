from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Tuple

from pygments.styles import get_style_by_name
from pygments.token import Token, TokenType, Text
from pygments.util import get_bool_opt, html_escape


def _ttype_to_css_long(ttype: TokenType) -> str:
    # Token.Name.Function -> "tok-Name-Function"
    if ttype is Token:
        return "tok-Token"
    parts = ttype.split()
    if not parts:
        return "tok-Token"
    return "tok-" + "-".join(parts)


_SHORT_MAP = {
    "Keyword": "k",
    "Keyword.Constant": "kc",
    "Name": "n",
    "Name.Function": "nf",
    "Name.Class": "nc",
    "Name.Decorator": "nd",
    "Name.Attribute": "na",
    "Name.Builtin": "nb",
    "Literal.String": "s",
    "Literal.String.Doc": "sd",
    "Literal.Number": "m",
    "Operator": "o",
    "Punctuation": "p",
    "Comment": "c",
    "Comment.Single": "c1",
    "Text": "",
}


def _ttype_to_short_class(ttype: TokenType) -> str:
    # find best match by walking up
    t = ttype
    while t is not None:
        key = repr(t)
        if key.startswith("Token."):
            key = key[6:]
        if key in _SHORT_MAP:
            return _SHORT_MAP[key]
        t = t.parent
    return ""


def _style_string_to_css(style: str) -> str:
    """
    Parse a tiny subset of Pygments style strings:
      'bold #rrggbb bg:#rrggbb italic underline'
    """
    if not style:
        return ""
    css: List[str] = []
    for part in style.split():
        if part == "bold":
            css.append("font-weight: bold")
        elif part == "italic":
            css.append("font-style: italic")
        elif part == "underline":
            css.append("text-decoration: underline")
        elif part.startswith("bg:"):
            css.append(f"background-color: {part[3:]}")
        elif part.startswith("#") and len(part) in (4, 7):
            css.append(f"color: {part}")
        # ignore unknown parts
    return "; ".join(css)


class HtmlFormatter:
    name = "HTML"
    aliases = ["html"]

    def __init__(self, **options):
        self.options = dict(options)
        self.nowrap = get_bool_opt(options, "nowrap", False)
        self.full = get_bool_opt(options, "full", False)
        self.noclasses = get_bool_opt(options, "noclasses", False)
        self.linenos = get_bool_opt(options, "linenos", False)  # minimal: unused
        self.cssclass = options.get("cssclass", "highlight")
        self.prestyles = options.get("prestyles", "")
        stylename = options.get("style", "default")
        self.style = get_style_by_name(stylename)

    def get_style_defs(self, arg: str = ".highlight") -> str:
        # Create CSS for known tokens present in style mapping plus a few common ones.
        rules: List[str] = []
        base = arg or ".highlight"

        bg = getattr(self.style, "background_color", None)
        if bg:
            rules.append(f"{base} {{ background: {bg}; }}")
        rules.append(f"{base} pre {{ margin: 0; }}")

        # Gather token types from the style class mapping if possible.
        token_types = set(getattr(self.style, "styles", {}).keys())
        # ensure some standard ones exist for tests
        from pygments.token import Keyword, Name, Literal, Comment, Number, Operator, Punctuation

        token_types.update([Text, Keyword, Keyword.Constant, Name, Name.Function, Name.Class, Name.Decorator,
                            Literal.String, Literal.String.Doc, Number, Comment, Operator, Punctuation])

        for ttype in sorted(token_types, key=lambda t: repr(t)):
            style_str = self.style.style_for_token(ttype)
            css = _style_string_to_css(style_str)
            if not css:
                continue
            longcls = _ttype_to_css_long(ttype)
            shortcls = _ttype_to_short_class(ttype)
            sels = [f"{base} .{longcls}"]
            if shortcls:
                sels.append(f"{base} .{shortcls}")
            rules.append(f"{', '.join(sels)} {{ {css}; }}")
        return "\n".join(rules) + ("\n" if rules else "")

    def _span(self, ttype: TokenType, value: str) -> str:
        esc = html_escape(value)
        if not esc:
            return ""
        if self.noclasses:
            style_str = self.style.style_for_token(ttype)
            css = _style_string_to_css(style_str)
            if css:
                return f'<span style="{css}">{esc}</span>'
            return esc
        longcls = _ttype_to_css_long(ttype)
        shortcls = _ttype_to_short_class(ttype)
        cls = longcls if not shortcls else f"{longcls} {shortcls}"
        return f'<span class="{cls}">{esc}</span>'

    def format(self, tokensource: Iterable[Tuple[TokenType, str]], outfile) -> Optional[str]:
        body_parts: List[str] = []
        for ttype, value in tokensource:
            # Don't wrap plain text with empty class if it is Text and no styling.
            if not self.noclasses and ttype in Text and not _ttype_to_short_class(ttype):
                body_parts.append(html_escape(value))
            else:
                body_parts.append(self._span(ttype, value))
        body = "".join(body_parts)

        if self.nowrap:
            outfile.write(body)
            return None

        prestyle_attr = f' style="{html_escape(self.prestyles)}"' if self.prestyles else ""
        wrapped = f'<div class="{html_escape(self.cssclass)}"><pre{prestyle_attr}>{body}</pre></div>'

        if self.full:
            css = self.get_style_defs(f".{self.cssclass}")
            doc = (
                "<!DOCTYPE html>\n"
                "<html>\n<head>\n"
                '<meta charset="utf-8" />\n'
                "<style>\n"
                f"{css}"
                "</style>\n"
                "</head>\n<body>\n"
                f"{wrapped}\n"
                "</body>\n</html>\n"
            )
            outfile.write(doc)
            return None

        outfile.write(wrapped)
        return None
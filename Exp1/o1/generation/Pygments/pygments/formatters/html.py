"""
HTML Formatter: outputs tokens wrapped in <span> tags with CSS classes.
"""

import sys
from io import StringIO

from . import Formatter, _formatters_by_name
from ..token import Token, Text
from ..styles import get_style_by_name
from ..util import option

class HtmlFormatter(Formatter):
    name = "html"

    def __init__(self, **options):
        super().__init__(**options)
        self.style = option(options.get("style"), "default")
        self.nowrap = option(options.get("nowrap"), False)
        self.noclasses = option(options.get("noclasses"), False)
        self.styledef = None

    def get_style_defs(self, arg=None):
        """
        Return the style definitions (as CSS).
        """
        if self.styledef is not None:
            return self.styledef

        style_class = get_style_by_name(self.style)
        lines = []
        for token_type, styledef in style_class.styles.items():
            if styledef:
                css_class = self._get_css_class(token_type)
                lines.append(".%s { %s }" % (css_class, self._css_from_style(styledef)))
        self.styledef = "\n".join(lines)
        return self.styledef

    def format(self, tokensource, outfile):
        """
        Convert the token source to formatted HTML.
        """
        if not self.nowrap:
            outfile.write("<div class=\"highlight\"><pre>")
        for ttype, value in tokensource:
            css_class = self._get_css_class(ttype)
            if self.noclasses:
                style_class = get_style_by_name(self.style)
                styledef = style_class.styles.get(ttype)
                if styledef:
                    style_text = self._css_from_style(styledef)
                    outfile.write("<span style=\"{}\">{}</span>".format(style_text, self._html_escape(value)))
                else:
                    outfile.write(self._html_escape(value))
            else:
                if css_class:
                    outfile.write("<span class=\"{}\">{}</span>".format(css_class, self._html_escape(value)))
                else:
                    outfile.write(self._html_escape(value))
        if not self.nowrap:
            outfile.write("</pre></div>")

    def _get_css_class(self, ttype):
        """
        Return a css class for the token.
        """
        # Flatten the token type for a stable lookup
        base = str(ttype).replace('.', '-')
        return "token-" + base.lower()

    @staticmethod
    def _css_from_style(styledef):
        """
        Convert Pygments-style tokens to inline CSS rules.
        Example styledef: "bold #00f bg:#fff"
        """
        parts = styledef.split()
        css_parts = []
        for part in parts:
            if part == 'bold':
                css_parts.append("font-weight: bold")
            elif part.startswith('#'):
                # treat as color
                css_parts.append("color: {}".format(part))
            elif part.startswith('bg:'):
                css_parts.append("background-color: {}".format(part[3:]))
        return "; ".join(css_parts)

    @staticmethod
    def _html_escape(text):
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

# register
_formatters_by_name["html"] = HtmlFormatter
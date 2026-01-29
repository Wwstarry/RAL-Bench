from ..token import Token, token_to_css_class, STANDARD_TYPES, is_token_subtype
from ..styles import get_style_by_name

def _html_escape(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def _parse_style_value(val):
    """
    Parse style value strings like "bold #008000 bg:#f8f8f8" into CSS.
    Also supports inline "color: #xxxxxx" fragments.
    """
    css = {}
    parts = [p.strip() for p in val.replace(";", " ").split() if p.strip()]
    for p in parts:
        if p.lower() == "bold":
            css["font-weight"] = "bold"
        elif p.lower() == "italic":
            css["font-style"] = "italic"
        elif p.lower() in ("underline", "underlined"):
            css["text-decoration"] = "underline"
        elif p.startswith("bg:"):
            css["background-color"] = p[3:]
        elif p.startswith("color:"):
            css["color"] = p.split(":", 1)[1]
        elif p.startswith("#"):
            css["color"] = p
    return css

def _css_dict_to_str(d):
    return "; ".join(f"{k}: {v}" for k, v in d.items())

class HtmlFormatter:
    """
    Minimal HTML Formatter.

    Options:
    - style: style name or class (default 'default')
    - noclasses: if True, use inline styles, else CSS classes
    """

    name = "HTML"

    def __init__(self, style="default", noclasses=False, **options):
        self.noclasses = bool(noclasses)
        self.options = options
        if isinstance(style, str):
            self.style = get_style_by_name(style)
        else:
            self.style = style

        # Build CSS map from style definitions
        self._style_map = {}
        for ttype, val in self.style.styles.items():
            css = _parse_style_value(val if isinstance(val, str) else str(val))
            self._style_map[ttype] = css

        # base text style default
        if Token.Text not in self._style_map:
            self._style_map[Token.Text] = {}

    def get_style_defs(self):
        """
        Return CSS style definitions for the current style.
        """
        # If noclasses, we don't produce separate CSS
        lines = []
        used_base_classes = set()
        # map STANDARD_TYPES to CSS classes
        for base_ttype, cls in STANDARD_TYPES.items():
            # compute CSS by finding best match: style for base token
            css = {}
            # start with exact match if available
            if base_ttype in self._style_map:
                css.update(self._style_map.get(base_ttype, {}))
            # else inherit from Text
            if not css:
                css.update(self._style_map.get(Token.Text, {}))
            if css:
                lines.append(f".{cls} {{ {_css_dict_to_str(css)} }}")
                used_base_classes.add(cls)
        # Also include Token.Error
        if Token.Error in self._style_map:
            lines.append(f".err {{ {_css_dict_to_str(self._style_map[Token.Error])} }}")
        return "\n".join(lines)

    def format(self, tokens, outfile):
        """
        Write formatted HTML output to outfile.
        """
        # Surround with a minimal container
        outfile.write('<div class="highlight"><pre>')
        for ttype, value in tokens:
            text = _html_escape(value)
            if not text:
                continue
            if self.noclasses:
                # inline style by best matching style
                style = self._resolve_inline_style(ttype)
                if style:
                    outfile.write(f'<span style="{style}">{text}</span>')
                else:
                    outfile.write(text)
            else:
                cls = token_to_css_class(ttype)
                outfile.write(f'<span class="{cls}">{text}</span>')
        outfile.write("</pre></div>")

    def _resolve_inline_style(self, ttype):
        # Search the closest matching style CSS dict
        # Walk up the token type hierarchy
        cur = ttype
        css = None
        while cur is not None:
            if cur in self._style_map:
                css = self._style_map[cur]
                break
            cur = cur.parent()
        if css:
            return _css_dict_to_str(css)
        return ""
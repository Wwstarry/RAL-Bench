from ..token import Token, STANDARD_TYPES, is_token_subtype
from ..util import get_bool_opt

RESET = "\x1b[0m"

# Simple ANSI colors mapping
ANSI_COLORS = {
    "black": "30",
    "red": "31",
    "green": "32",
    "yellow": "33",
    "blue": "34",
    "magenta": "35",
    "cyan": "36",
    "white": "37",
    "bright_black": "90",
    "bright_red": "91",
    "bright_green": "92",
    "bright_yellow": "93",
    "bright_blue": "94",
    "bright_magenta": "95",
    "bright_cyan": "96",
    "bright_white": "97",
}

DEFAULT_TOKEN_COLORS = {
    Token.Text: None,
    Token.Whitespace: None,
    Token.Error: ("red", True),
    Token.Comment: ("bright_black", False),
    Token.Keyword: ("green", True),
    Token.Name: ("white", False),
    Token.String: ("red", False),
    Token.Number: ("cyan", False),
    Token.Operator: ("magenta", False),
    Token.Punctuation: ("white", False),
    Token.Generic: ("white", False),
}

class TerminalFormatter:
    """
    Minimal terminal formatter that emits ANSI-colored output.

    Options:
    - colors: enable colored output (default True)
    """

    name = "Terminal"

    def __init__(self, **options):
        self.colors = get_bool_opt(options, "colors", True)

    def _style_for_token(self, ttype):
        # find the closest color mapping
        cur = ttype
        while cur is not None:
            if cur in DEFAULT_TOKEN_COLORS:
                return DEFAULT_TOKEN_COLORS[cur]
            cur = cur.parent()
        return None

    def _ansi_seq(self, color_name, bold=False):
        codes = []
        if bold:
            codes.append("1")
        if color_name:
            code = ANSI_COLORS.get(color_name, ANSI_COLORS["white"])
            codes.append(code)
        if not codes:
            return ""
        return "\x1b[" + ";".join(codes) + "m"

    def format(self, tokens, outfile):
        for ttype, value in tokens:
            if self.colors:
                style = self._style_for_token(ttype)
                if style:
                    color_name, bold = style
                    outfile.write(self._ansi_seq(color_name, bold))
                    outfile.write(value)
                    outfile.write(RESET)
                else:
                    outfile.write(value)
            else:
                outfile.write(value)
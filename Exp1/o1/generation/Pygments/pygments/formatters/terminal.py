"""
Terminal Formatter: outputs tokens with ANSI color codes.
"""

from . import Formatter, _formatters_by_name
from ..token import Token, Text, Keyword, Name, Comment, String, Number, Operator, Punctuation

ANSI_CODES = {
    Text:        "",
    Keyword:     "\033[94m",  # bright blue
    Name:        "\033[92m",  # bright green
    Comment:     "\033[90m",  # dark grey
    String:      "\033[91m",  # bright red
    Number:      "\033[95m",  # bright magenta
    Operator:    "\033[93m",  # bright yellow
    Punctuation: "\033[93m",  # bright yellow
}

ANSI_RESET = "\033[0m"

class TerminalFormatter(Formatter):
    name = "terminal"

    def __init__(self, **options):
        super().__init__(**options)
        self.strip = options.get("strip", False)
        self.bg = options.get("bg", None)
        self.colormap = dict(ANSI_CODES)

    def format(self, tokensource, outfile):
        for ttype, value in tokensource:
            color = self.colormap.get(ttype)
            if color is None:
                # fallback to supertype
                color = self._lookup_supertype(ttype)
            if color is None:
                color = ""
            if self.strip:
                outfile.write(value)
            else:
                outfile.write(color + value + ANSI_RESET)

    def _lookup_supertype(self, ttype):
        # naive supertype approach
        for known in ANSI_CODES.keys():
            if str(ttype).startswith(str(known)):
                return ANSI_CODES[known]
        return ""

# register
_formatters_by_name["terminal"] = TerminalFormatter
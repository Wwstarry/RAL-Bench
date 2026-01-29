from collections import namedtuple

# Configuration for a table line (horizontal rule)
# begin: char at start of line
# hline: char for the horizontal line
# sep: char at intersection of columns
# end: char at end of line
Line = namedtuple("Line", ["begin", "hline", "sep", "end"])

# Configuration for a data row
# begin: char at start of row
# sep: char separating columns
# end: char at end of row
DataRow = namedtuple("DataRow", ["begin", "sep", "end"])

# Complete table format definition
TableFormat = namedtuple("TableFormat", [
    "lineabove",        # Line or None
    "linebelowheader",  # Line or None
    "linebetweenrows",  # Line or None
    "linebelow",        # Line or None
    "headerrow",        # DataRow
    "datarow",          # DataRow
    "padding",          # int (padding width)
    "with_header_hide", # list of strings (optional, not strictly used in minimal impl but good for compat)
])

_formats = {}

def _register(name, lineabove, linebelowheader, linebetweenrows, linebelow, headerrow, datarow, padding, with_header_hide=None):
    _formats[name] = TableFormat(
        lineabove, linebelowheader, linebetweenrows, linebelow, headerrow, datarow, padding, with_header_hide
    )

# --- Format Definitions ---

# plain: No borders, just columns
_register("plain",
          None, None, None, None,
          DataRow("", "  ", ""),
          DataRow("", "  ", ""),
          0)

# simple: Dashes below header, standard spacing
_register("simple",
          None,
          Line("", "-", "  ", ""),
          None,
          None,
          DataRow("", "  ", ""),
          DataRow("", "  ", ""),
          0)

# grid: Full ASCII grid
_register("grid",
          Line("+", "-", "+", "+"),
          Line("+", "=", "+", "+"),
          Line("+", "-", "+", "+"),
          Line("+", "-", "+", "+"),
          DataRow("|", "|", "|"),
          DataRow("|", "|", "|"),
          1)

# simple_grid: Grid without header distinction
_register("simple_grid",
          Line("+", "-", "+", "+"),
          Line("+", "-", "+", "+"),
          Line("+", "-", "+", "+"),
          Line("+", "-", "+", "+"),
          DataRow("|", "|", "|"),
          DataRow("|", "|", "|"),
          1)

# rounded_grid: Grid with rounded corners (approximated with ASCII for compatibility if unicode not requested, 
# but here we stick to standard chars or simple unicode if needed. Keeping it ASCII for safety).
_register("rounded_grid",
          Line("╭", "─", "┬", "╮"),
          Line("├", "─", "┼", "┤"),
          Line("├", "─", "┼", "┤"),
          Line("╰", "─", "┴", "╯"),
          DataRow("│", "│", "│"),
          DataRow("│", "│", "│"),
          1)

# pipe: Markdown style
_register("pipe",
          None,
          Line("|", "-", "|", "|"),
          None,
          None,
          DataRow("|", "|", "|"),
          DataRow("|", "|", "|"),
          1)

# orgtbl: Emacs org-mode
_register("orgtbl",
          None,
          Line("|", "-", "+", "|"),
          None,
          None,
          DataRow("|", "|", "|"),
          DataRow("|", "|", "|"),
          1)

# rst: ReStructuredText
_register("rst",
          Line("", "=", "  ", ""),
          Line("", "=", "  ", ""),
          None,
          Line("", "=", "  ", ""),
          DataRow("", "  ", ""),
          DataRow("", "  ", ""),
          0)

# mediawiki
_register("mediawiki",
          Line("{| class=\"wikitable\"", "", "", ""),
          Line("|-", "", "", ""),
          Line("|-", "", "", ""),
          Line("|}", "", "", ""),
          DataRow("!", "!!", ""),
          DataRow("|", "||", ""),
          1)

# html: Standard HTML table
_register("html",
          Line("<table>", "", "", ""),
          None,
          None,
          Line("</table>", "", "", ""),
          DataRow("<tr><th>", "</th><th>", "</th></tr>"),
          DataRow("<tr><td>", "</td><td>", "</td></tr>"),
          0)

# tsv: Tab separated
_register("tsv",
          None, None, None, None,
          DataRow("", "\t", ""),
          DataRow("", "\t", ""),
          0)

tabulate_formats = list(_formats.keys())
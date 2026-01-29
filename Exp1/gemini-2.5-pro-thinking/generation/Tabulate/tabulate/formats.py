from collections import namedtuple

TableFormat = namedtuple(
    "TableFormat",
    [
        "lineabove",
        "linebelowheader",
        "linebetweenrows",
        "linebelow",
        "headerrow",
        "datarow",
        "padding",
        "with_header_hide",
    ],
)

Line = namedtuple("Line", ["begin", "hline", "sep", "end"])
Row = namedtuple("Row", ["begin", "sep", "end"])

_plain_row = Row("", "  ", "")
_pipe_row = Row("| ", " | ", " |")
_grid_row = Row("| ", " | ", " |")
_fancy_grid_row = Row("│ ", " │ ", " │")

_table_formats = {
    "plain": TableFormat(
        lineabove=None,
        linebelowheader=None,
        linebetweenrows=None,
        linebelow=None,
        headerrow=_plain_row,
        datarow=_plain_row,
        padding=0,
        with_header_hide=None,
    ),
    "simple": TableFormat(
        lineabove=Line("", "-", "  ", ""),
        linebelowheader=Line("", "-", "  ", ""),
        linebetweenrows=None,
        linebelow=Line("", "-", "  ", ""),
        headerrow=_plain_row,
        datarow=_plain_row,
        padding=0,
        with_header_hide=["lineabove", "linebelow"],
    ),
    "grid": TableFormat(
        lineabove=Line("+", "-", "+", "+"),
        linebelowheader=Line("+", "=", "+", "+"),
        linebetweenrows=Line("+", "-", "+", "+"),
        linebelow=Line("+", "-", "+", "+"),
        headerrow=_grid_row,
        datarow=_grid_row,
        padding=1,
        with_header_hide=None,
    ),
    "fancy_grid": TableFormat(
        lineabove=Line("┌", "─", "┬", "┐"),
        linebelowheader=Line("├", "═", "╪", "┤"),
        linebetweenrows=Line("├", "─", "┼", "┤"),
        linebelow=Line("└", "─", "┴", "┘"),
        headerrow=_fancy_grid_row,
        datarow=_fancy_grid_row,
        padding=1,
        with_header_hide=None,
    ),
    "pipe": TableFormat(
        lineabove=None,
        linebelowheader=Line("|", "-", "|", "|"),
        linebetweenrows=None,
        linebelow=None,
        headerrow=_pipe_row,
        datarow=_pipe_row,
        padding=1,
        with_header_hide=["linebelowheader"],
    ),
    "orgtbl": TableFormat(
        lineabove=None,
        linebelowheader=Line("|", "-", "+", "|"),
        linebetweenrows=None,
        linebelow=None,
        headerrow=_pipe_row,
        datarow=_pipe_row,
        padding=1,
        with_header_hide=["linebelowheader"],
    ),
    "jira": TableFormat(
        lineabove=None,
        linebelowheader=Line("||", "=", "||", "||"),
        linebetweenrows=None,
        linebelow=None,
        headerrow=Row("|| ", " || ", " ||"),
        datarow=Row("| ", " | ", " |"),
        padding=1,
        with_header_hide=["linebelowheader"],
    ),
    "presto": TableFormat(
        lineabove=None,
        linebelowheader=Line("", "-", "+", ""),
        linebetweenrows=None,
        linebelow=None,
        headerrow=Row("", " | ", ""),
        datarow=Row("", " | ", ""),
        padding=1,
        with_header_hide=["linebelowheader"],
    ),
    "pretty": TableFormat(
        lineabove=Line("+", "-", "-", "+"),
        linebelowheader=Line("+", "-", "-", "+"),
        linebetweenrows=None,
        linebelow=Line("+", "-", "-", "+"),
        headerrow=Row("| ", " ", " |"),
        datarow=Row("| ", " ", " |"),
        padding=1,
        with_header_hide=None,
    ),
    "psql": TableFormat(
        lineabove=Line("+", "-", "+", "+"),
        linebelowheader=Line("|", "-", "+", "|"),
        linebetweenrows=None,
        linebelow=Line("+", "-", "+", "+"),
        headerrow=Row("| ", " | ", " |"),
        datarow=Row("| ", " | ", " |"),
        padding=1,
        with_header_hide=None,
    ),
    "rst": TableFormat(
        lineabove=Line("", "=", "  ", ""),
        linebelowheader=Line("", "=", "  ", ""),
        linebetweenrows=None,
        linebelow=Line("", "=", "  ", ""),
        headerrow=Row("", "  ", ""),
        datarow=Row("", "  ", ""),
        padding=0,
        with_header_hide=None,
    ),
    "html": TableFormat(
        lineabove=Line("<table>", "", "", ""),
        linebelowheader=None,
        linebetweenrows=None,
        linebelow=Line("</table>", "", "", ""),
        headerrow=Row("<thead>\n<tr><th>", "</th><th>", "</th></tr>\n</thead>\n<tbody>"),
        datarow=Row("<tr><td>", "</td><td>", "</td></tr>"),
        padding=0,
        with_header_hide=["headerrow"],
    ),
    "tsv": TableFormat(
        lineabove=None,
        linebelowheader=None,
        linebetweenrows=None,
        linebelow=None,
        headerrow=Row("", "\t", ""),
        datarow=Row("", "\t", ""),
        padding=0,
        with_header_hide=None,
    ),
}

def simple_separated_format(separator):
    """
    Create a simple table format that uses a given separator.
    """
    return TableFormat(
        lineabove=None,
        linebelowheader=None,
        linebetweenrows=None,
        linebelow=None,
        headerrow=Row("", separator, ""),
        datarow=Row("", separator, ""),
        padding=0,
        with_header_hide=None,
    )
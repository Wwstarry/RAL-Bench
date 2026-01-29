"""
Core tabulation functionality
"""

import re
from collections import namedtuple
from collections.abc import Mapping
from html import escape as html_escape
from itertools import zip_longest


# Named tuples for table structure
Line = namedtuple("Line", ["begin", "hline", "sep", "end"])
DataRow = namedtuple("DataRow", ["begin", "sep", "end"])


class TableFormat:
    """Defines the formatting of a table"""
    
    def __init__(self, lineabove, linebelowheader, linebetweenrows, linebelow,
                 headerrow, datarow, padding, with_header_hide=None):
        self.lineabove = lineabove
        self.linebelowheader = linebelowheader
        self.linebetweenrows = linebetweenrows
        self.linebelow = linebelow
        self.headerrow = headerrow
        self.datarow = datarow
        self.padding = padding
        self.with_header_hide = with_header_hide or []


# Predefined table formats
_table_formats = {
    "plain": TableFormat(
        lineabove=None,
        linebelowheader=None,
        linebetweenrows=None,
        linebelow=None,
        headerrow=DataRow("", "  ", ""),
        datarow=DataRow("", "  ", ""),
        padding=0,
        with_header_hide=["lineabove", "linebelow"]
    ),
    "simple": TableFormat(
        lineabove=Line("", "-", "  ", ""),
        linebelowheader=Line("", "-", "  ", ""),
        linebetweenrows=None,
        linebelow=Line("", "-", "  ", ""),
        headerrow=DataRow("", "  ", ""),
        datarow=DataRow("", "  ", ""),
        padding=0,
        with_header_hide=["lineabove"]
    ),
    "grid": TableFormat(
        lineabove=Line("+", "-", "+", "+"),
        linebelowheader=Line("+", "=", "+", "+"),
        linebetweenrows=Line("+", "-", "+", "+"),
        linebelow=Line("+", "-", "+", "+"),
        headerrow=DataRow("|", "|", "|"),
        datarow=DataRow("|", "|", "|"),
        padding=1,
        with_header_hide=[]
    ),
    "fancy_grid": TableFormat(
        lineabove=Line("╒", "═", "╤", "╕"),
        linebelowheader=Line("╞", "═", "╪", "╡"),
        linebetweenrows=Line("├", "─", "┼", "┤"),
        linebelow=Line("╘", "═", "╧", "╛"),
        headerrow=DataRow("│", "│", "│"),
        datarow=DataRow("│", "│", "│"),
        padding=1,
        with_header_hide=[]
    ),
    "pipe": TableFormat(
        lineabove=None,
        linebelowheader=Line("|", "-", "|", "|"),
        linebetweenrows=None,
        linebelow=None,
        headerrow=DataRow("|", "|", "|"),
        datarow=DataRow("|", "|", "|"),
        padding=1,
        with_header_hide=["lineabove", "linebelow"]
    ),
    "orgtbl": TableFormat(
        lineabove=None,
        linebelowheader=Line("|", "-", "+", "|"),
        linebetweenrows=None,
        linebelow=None,
        headerrow=DataRow("|", "|", "|"),
        datarow=DataRow("|", "|", "|"),
        padding=1,
        with_header_hide=["lineabove", "linebelow"]
    ),
    "jira": TableFormat(
        lineabove=None,
        linebelowheader=None,
        linebetweenrows=None,
        linebelow=None,
        headerrow=DataRow("||", "||", "||"),
        datarow=DataRow("|", "|", "|"),
        padding=1,
        with_header_hide=["lineabove", "linebelow"]
    ),
    "presto": TableFormat(
        lineabove=None,
        linebelowheader=Line("", "-", "+", ""),
        linebetweenrows=None,
        linebelow=None,
        headerrow=DataRow("", "|", ""),
        datarow=DataRow("", "|", ""),
        padding=1,
        with_header_hide=["lineabove", "linebelow"]
    ),
    "pretty": TableFormat(
        lineabove=Line("+", "-", "+", "+"),
        linebelowheader=Line("+", "-", "+", "+"),
        linebetweenrows=None,
        linebelow=Line("+", "-", "+", "+"),
        headerrow=DataRow("|", "|", "|"),
        datarow=DataRow("|", "|", "|"),
        padding=1,
        with_header_hide=[]
    ),
    "psql": TableFormat(
        lineabove=Line("+", "-", "+", "+"),
        linebelowheader=Line("|", "-", "+", "|"),
        linebetweenrows=None,
        linebelow=Line("+", "-", "+", "+"),
        headerrow=DataRow("|", "|", "|"),
        datarow=DataRow("|", "|", "|"),
        padding=1,
        with_header_hide=[]
    ),
    "rst": TableFormat(
        lineabove=Line("", "=", "  ", ""),
        linebelowheader=Line("", "=", "  ", ""),
        linebetweenrows=None,
        linebelow=Line("", "=", "  ", ""),
        headerrow=DataRow("", "  ", ""),
        datarow=DataRow("", "  ", ""),
        padding=0,
        with_header_hide=[]
    ),
    "mediawiki": TableFormat(
        lineabove=Line("{| class=\"wikitable\" style=\"text-align: left;\"", "", "", ""),
        linebelowheader=Line("|-", "", "", ""),
        linebetweenrows=Line("|-", "", "", ""),
        linebelow=Line("|}", "", "", ""),
        headerrow=DataRow("!", "!!", ""),
        datarow=DataRow("|", "||", ""),
        padding=0,
        with_header_hide=[]
    ),
    "moinmoin": TableFormat(
        lineabove=None,
        linebelowheader=None,
        linebetweenrows=None,
        linebelow=None,
        headerrow=DataRow("||", "||", "||"),
        datarow=DataRow("||", "||", "||"),
        padding=1,
        with_header_hide=["lineabove", "linebelow"]
    ),
    "youtrack": TableFormat(
        lineabove=None,
        linebelowheader=None,
        linebetweenrows=None,
        linebelow=None,
        headerrow=DataRow("||", "||", "||"),
        datarow=DataRow("|", "|", "|"),
        padding=1,
        with_header_hide=["lineabove", "linebelow"]
    ),
    "html": TableFormat(
        lineabove=Line("<table>", "", "", ""),
        linebelowheader=None,
        linebetweenrows=None,
        linebelow=Line("</table>", "", "", ""),
        headerrow=DataRow("<tr><th>", "</th><th>", "</th></tr>"),
        datarow=DataRow("<tr><td>", "</td><td>", "</td></tr>"),
        padding=0,
        with_header_hide=[]
    ),
    "unsafehtml": TableFormat(
        lineabove=Line("<table>", "", "", ""),
        linebelowheader=None,
        linebetweenrows=None,
        linebelow=Line("</table>", "", "", ""),
        headerrow=DataRow("<tr><th>", "</th><th>", "</th></tr>"),
        datarow=DataRow("<tr><td>", "</td><td>", "</td></tr>"),
        padding=0,
        with_header_hide=[]
    ),
    "latex": TableFormat(
        lineabove=Line("\\begin{tabular}", "", "", ""),
        linebelowheader=Line("\\hline", "", "", ""),
        linebetweenrows=None,
        linebelow=Line("\\end{tabular}", "", "", ""),
        headerrow=DataRow("", "&", "\\\\"),
        datarow=DataRow("", "&", "\\\\"),
        padding=1,
        with_header_hide=[]
    ),
    "latex_raw": TableFormat(
        lineabove=Line("\\begin{tabular}", "", "", ""),
        linebelowheader=Line("\\hline", "", "", ""),
        linebetweenrows=None,
        linebelow=Line("\\end{tabular}", "", "", ""),
        headerrow=DataRow("", "&", "\\\\"),
        datarow=DataRow("", "&", "\\\\"),
        padding=1,
        with_header_hide=[]
    ),
    "latex_booktabs": TableFormat(
        lineabove=Line("\\begin{tabular}", "", "", ""),
        linebelowheader=Line("\\midrule", "", "", ""),
        linebetweenrows=None,
        linebelow=Line("\\end{tabular}", "", "", ""),
        headerrow=DataRow("", "&", "\\\\"),
        datarow=DataRow("", "&", "\\\\"),
        padding=1,
        with_header_hide=[]
    ),
    "textile": TableFormat(
        lineabove=None,
        linebelowheader=None,
        linebetweenrows=None,
        linebelow=None,
        headerrow=DataRow("|_.", "|_.", "|"),
        datarow=DataRow("|", "|", "|"),
        padding=1,
        with_header_hide=["lineabove", "linebelow"]
    ),
    "tsv": TableFormat(
        lineabove=None,
        linebelowheader=None,
        linebetweenrows=None,
        linebelow=None,
        headerrow=DataRow("", "\t", ""),
        datarow=DataRow("", "\t", ""),
        padding=0,
        with_header_hide=["lineabove", "linebelow"]
    ),
}


def simple_separated_format(separator):
    """Return a simple table format with a custom separator"""
    return TableFormat(
        lineabove=None,
        linebelowheader=None,
        linebetweenrows=None,
        linebelow=None,
        headerrow=DataRow("", separator, ""),
        datarow=DataRow("", separator, ""),
        padding=0,
        with_header_hide=["lineabove", "linebelow"]
    )


def _is_separating_line(row):
    """Check if a row is a separating line"""
    return isinstance(row, (Line, type(None)))


def _normalize_tabular_data(tabular_data, headers):
    """Convert various input formats to a list of lists"""
    if hasattr(tabular_data, "keys") and hasattr(tabular_data, "values"):
        # Dictionary
        if headers == "keys":
            headers = list(tabular_data.keys())
        rows = [list(tabular_data.values())]
        return rows, headers
    
    if not tabular_data:
        return [], headers
    
    # Check if it's a list of dicts
    if isinstance(tabular_data, list) and len(tabular_data) > 0:
        if isinstance(tabular_data[0], Mapping):
            # List of dicts
            if headers == "keys":
                headers = list(tabular_data[0].keys())
            rows = []
            for item in tabular_data:
                if headers:
                    row = [item.get(h, "") for h in headers]
                else:
                    row = list(item.values())
                rows.append(row)
            return rows, headers
    
    # Convert to list of lists
    rows = [list(row) if not isinstance(row, str) else [row] for row in tabular_data]
    return rows, headers


def _format_cell(cell, width, align, is_multiline=False):
    """Format a single cell with alignment and padding"""
    if cell is None:
        cell = ""
    
    cell_str = str(cell)
    
    if is_multiline:
        lines = cell_str.splitlines()
        formatted_lines = []
        for line in lines:
            if align == "right":
                formatted_lines.append(line.rjust(width))
            elif align == "center":
                formatted_lines.append(line.center(width))
            else:  # left
                formatted_lines.append(line.ljust(width))
        return formatted_lines
    else:
        if align == "right":
            return cell_str.rjust(width)
        elif align == "center":
            return cell_str.center(width)
        else:  # left
            return cell_str.ljust(width)


def _visible_width(s):
    """Calculate visible width of a string (excluding ANSI codes)"""
    # Remove ANSI escape sequences
    ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
    return len(ansi_escape.sub('', str(s)))


def _align_column(strings, alignment, width=None):
    """Align a column of strings"""
    if not strings:
        return strings
    
    if width is None:
        width = max(_visible_width(s) for s in strings)
    
    aligned = []
    for s in strings:
        s_str = str(s) if s is not None else ""
        visible = _visible_width(s_str)
        padding = width - visible
        
        if alignment == "right":
            aligned.append(" " * padding + s_str)
        elif alignment == "center":
            left_pad = padding // 2
            right_pad = padding - left_pad
            aligned.append(" " * left_pad + s_str + " " * right_pad)
        else:  # left
            aligned.append(s_str + " " * padding)
    
    return aligned


def _infer_alignment(column_data):
    """Infer alignment based on column data types"""
    # Check if all non-None values are numeric
    for val in column_data:
        if val is None or val == "":
            continue
        if isinstance(val, (int, float)):
            continue
        try:
            float(str(val))
        except (ValueError, TypeError):
            return "left"
    return "right"


def _build_simple_row(padded_cells, begin, sep, end):
    """Build a simple row from padded cells"""
    if not padded_cells:
        return begin + end
    return begin + sep.join(padded_cells) + end


def _build_line(colwidths, line_format):
    """Build a horizontal line"""
    if line_format is None:
        return None
    
    cells = [line_format.hline * width for width in colwidths]
    return _build_simple_row(cells, line_format.begin, line_format.sep, line_format.end)


def _pad_row(cells, num_cols):
    """Pad a row to have the correct number of columns"""
    if len(cells) < num_cols:
        return list(cells) + [""] * (num_cols - len(cells))
    return list(cells)


def _escape_html(cell, is_unsafe=False):
    """Escape HTML in cell content"""
    if is_unsafe:
        return str(cell) if cell is not None else ""
    return html_escape(str(cell)) if cell is not None else ""


def _escape_latex(cell):
    """Escape LaTeX special characters"""
    s = str(cell) if cell is not None else ""
    replacements = {
        "\\": "\\textbackslash{}",
        "{": "\\{",
        "}": "\\}",
        "$": "\\$",
        "&": "\\&",
        "%": "\\%",
        "#": "\\#",
        "_": "\\_",
        "~": "\\textasciitilde{}",
        "^": "\\textasciicircum{}",
    }
    for old, new in replacements.items():
        s = s.replace(old, new)
    return s


def tabulate(tabular_data, headers=(), tablefmt="simple", floatfmt="g",
             numalign="decimal", stralign="left", missingval="",
             showindex="default", disable_numparse=False, colalign=None):
    """
    Format a table for pretty-printing.
    
    Args:
        tabular_data: A list of lists, list of dicts, or dict
        headers: List of column headers or "keys", "firstrow"
        tablefmt: Table format name or TableFormat object
        floatfmt: Float format string
        numalign: Alignment for numbers ("decimal", "right", "center", "left")
        stralign: Alignment for strings
        missingval: Value to use for missing data
        showindex: Whether to show row indices
        disable_numparse: Disable automatic number parsing
        colalign: List of column alignments
    
    Returns:
        Formatted table as a string
    """
    
    # Handle table format
    if isinstance(tablefmt, str):
        if tablefmt in _table_formats:
            fmt = _table_formats[tablefmt]
        else:
            # Assume it's a separator for simple_separated_format
            fmt = simple_separated_format(tablefmt)
    elif isinstance(tablefmt, TableFormat):
        fmt = tablefmt
    else:
        fmt = _table_formats["simple"]
    
    # Normalize data
    rows, headers = _normalize_tabular_data(tabular_data, headers)
    
    if not rows and not headers:
        return ""
    
    # Handle headers
    if headers == "firstrow" and rows:
        headers = rows[0]
        rows = rows[1:]
    
    # Determine number of columns
    num_cols = 0
    if headers:
        num_cols = len(headers)
    if rows:
        num_cols = max(num_cols, max(len(row) for row in rows))
    
    if num_cols == 0:
        return ""
    
    # Pad all rows
    if headers:
        headers = _pad_row(headers, num_cols)
    rows = [_pad_row(row, num_cols) for row in rows]
    
    # Handle missing values
    if missingval != "":
        rows = [[missingval if cell == "" or cell is None else cell for cell in row] for row in rows]
        if headers:
            headers = [missingval if cell == "" or cell is None else cell for cell in headers]
    
    # Handle HTML escaping
    is_html = tablefmt in ["html"]
    is_unsafe_html = tablefmt in ["unsafehtml"]
    is_latex = tablefmt in ["latex", "latex_booktabs"]
    is_latex_raw = tablefmt in ["latex_raw"]
    
    if is_html:
        rows = [[_escape_html(cell, False) for cell in row] for row in rows]
        if headers:
            headers = [_escape_html(cell, False) for cell in headers]
    elif is_unsafe_html:
        rows = [[_escape_html(cell, True) for cell in row] for row in rows]
        if headers:
            headers = [_escape_html(cell, True) for cell in headers]
    elif is_latex:
        rows = [[_escape_latex(cell) for cell in row] for row in rows]
        if headers:
            headers = [_escape_latex(cell) for cell in headers]
    
    # Convert all cells to strings
    str_rows = []
    for row in rows:
        str_row = []
        for cell in row:
            if cell is None:
                str_row.append("")
            elif isinstance(cell, float):
                str_row.append(format(cell, floatfmt))
            else:
                str_row.append(str(cell))
        str_rows.append(str_row)
    
    if headers:
        str_headers = [str(h) if h is not None else "" for h in headers]
    else:
        str_headers = None
    
    # Calculate column widths
    colwidths = [0] * num_cols
    
    if str_headers:
        for i, h in enumerate(str_headers):
            colwidths[i] = max(colwidths[i], _visible_width(h))
    
    for row in str_rows:
        for i, cell in enumerate(row):
            colwidths[i] = max(colwidths[i], _visible_width(cell))
    
    # Determine alignments
    if colalign:
        alignments = list(colalign)
        while len(alignments) < num_cols:
            alignments.append(stralign)
    else:
        alignments = []
        for col_idx in range(num_cols):
            col_data = [row[col_idx] for row in rows if col_idx < len(row)]
            if not disable_numparse:
                alignment = _infer_alignment(col_data)
                if alignment == "right":
                    alignments.append(numalign if numalign != "decimal" else "right")
                else:
                    alignments.append(stralign)
            else:
                alignments.append(stralign)
    
    # Align columns
    aligned_rows = []
    for row in str_rows:
        aligned_row = []
        for i, cell in enumerate(row):
            aligned_cell = _align_column([cell], alignments[i], colwidths[i])[0]
            aligned_row.append(aligned_cell)
        aligned_rows.append(aligned_row)
    
    if str_headers:
        aligned_headers = []
        for i, h in enumerate(str_headers):
            aligned_h = _align_column([h], alignments[i], colwidths[i])[0]
            aligned_headers.append(aligned_h)
    else:
        aligned_headers = None
    
    # Add padding
    if fmt.padding > 0:
        pad = " " * fmt.padding
        colwidths = [w + 2 * fmt.padding for w in colwidths]
        
        if aligned_headers:
            aligned_headers = [pad + h + pad for h in aligned_headers]
        
        aligned_rows = [[pad + cell + pad for cell in row] for row in aligned_rows]
    
    # Build output
    lines = []
    
    # Line above
    if fmt.lineabove and (aligned_headers or "lineabove" not in fmt.with_header_hide):
        line = _build_line(colwidths, fmt.lineabove)
        if line:
            lines.append(line)
    
    # Header row
    if aligned_headers:
        header_line = _build_simple_row(aligned_headers, fmt.headerrow.begin,
                                       fmt.headerrow.sep, fmt.headerrow.end)
        lines.append(header_line)
        
        # Line below header
        if fmt.linebelowheader:
            line = _build_line(colwidths, fmt.linebelowheader)
            if line:
                lines.append(line)
    
    # Data rows
    for i, row in enumerate(aligned_rows):
        row_line = _build_simple_row(row, fmt.datarow.begin,
                                     fmt.datarow.sep, fmt.datarow.end)
        lines.append(row_line)
        
        # Line between rows
        if fmt.linebetweenrows and i < len(aligned_rows) - 1:
            line = _build_line(colwidths, fmt.linebetweenrows)
            if line:
                lines.append(line)
    
    # Line below
    if fmt.linebelow and (aligned_headers or "linebelow" not in fmt.with_header_hide):
        line = _build_line(colwidths, fmt.linebelow)
        if line:
            lines.append(line)
    
    return "\n".join(lines)
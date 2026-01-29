import re
from collections.abc import Iterable, Mapping
from .formats import _table_formats, simple_separated_format, Line, Row

# Add common aliases to the format map if they don't exist
if "github" not in _table_formats:
    _table_formats["github"] = _table_formats["pipe"]
if "markdown" not in _table_formats:
    _table_formats["markdown"] = _table_formats["pipe"]


def _is_number(s):
    """Check if a string is a number."""
    if isinstance(s, (int, float)):
        return True
    try:
        float(str(s))
        return True
    except (ValueError, TypeError):
        return False


def _strip_ansi(s):
    """Remove ANSI escape sequences from a string."""
    if not isinstance(s, str):
        return s
    return re.sub(r"\x1b\[[;\d]*[A-Za-z]", "", s)


def _visible_width(s):
    """Return the visible width of a string, accounting for ANSI codes."""
    return len(_strip_ansi(s))


def _align_string(s, width, alignment):
    """Align a string within a given width."""
    visible_len = _visible_width(s)
    pad = width - visible_len
    if alignment == "left":
        return s + " " * pad
    elif alignment == "right":
        return " " * pad + s
    elif alignment == "center":
        left_pad = pad // 2
        right_pad = pad - left_pad
        return " " * left_pad + s + " " * right_pad
    return s


def _normalize_tabular_data(tabular_data, headers, showindex="default"):
    """Convert various data formats to a list of lists and headers."""
    if isinstance(tabular_data, Mapping):
        # It's a dict of iterables
        keys = list(tabular_data.keys())
        if not headers:
            headers = keys
        
        vals = [list(v) if isinstance(v, Iterable) and not isinstance(v, str) else [v] for v in tabular_data.values()]
        max_len = max(len(v) for v in vals) if vals else 0
        data = [[(v[i] if i < len(v) else None) for v in vals] for i in range(max_len)]
        
    elif isinstance(tabular_data, Iterable) and not isinstance(tabular_data, str):
        rows = list(tabular_data)
        if rows and all(isinstance(row, Mapping) for row in rows):
            # It's a list of dicts
            if not headers:
                # Use keys from the first dict as headers, preserving order
                unique_headers = set()
                ordered_headers = []
                for row in rows:
                    for key in row.keys():
                        if key not in unique_headers:
                            unique_headers.add(key)
                            ordered_headers.append(key)
                headers = ordered_headers

            data = [[row.get(h) for h in headers] for row in rows]
        else:
            # Assume it's a list of lists or other iterable of iterables
            data = [list(row) for row in rows]
    else:
        data = [[tabular_data]]

    # Handle showindex
    if showindex == "always" or (showindex == "default" and headers):
        if not headers:
            num_cols = len(data[0]) if data else 0
            headers = [""] * num_cols
        headers.insert(0, "")
        for i, row in enumerate(data):
            row.insert(0, i)
            
    return list(headers), data


def _str_format(val, floatfmt, missingval):
    """Format a single value into a string."""
    if val is None:
        return missingval
    if isinstance(val, float):
        return format(val, floatfmt)
    return str(val)


def _process_data(headers, data, colalign, numalign, stralign, floatfmt, missingval):
    """Convert all data to strings and determine column alignments."""
    string_headers = [_str_format(h, floatfmt, missingval) for h in headers]
    string_rows = [[_str_format(v, floatfmt, missingval) for v in row] for row in data]
    
    num_cols = len(string_headers) if string_headers else (len(string_rows[0]) if string_rows else 0)
    
    # Determine column alignments
    aligns = list(colalign) if colalign else [None] * num_cols

    col_is_numeric = [True] * num_cols
    for row in string_rows:
        for i, cell in enumerate(row):
            if i < len(col_is_numeric) and not _is_number(cell):
                col_is_numeric[i] = False

    for i in range(num_cols):
        if aligns[i] is None:
            aligns[i] = numalign if col_is_numeric[i] else stralign
            
    return string_headers, string_rows, aligns


def _get_column_widths(headers, rows):
    """Calculate column widths for multiline content."""
    num_cols = len(headers) if headers else (len(rows[0]) if rows else 0)
    widths = [0] * num_cols
    
    if headers:
        for i, h in enumerate(headers):
            widths[i] = max(widths[i], max((_visible_width(line) for line in h.splitlines()), default=0))
            
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(widths):
                widths[i] = max(widths[i], max((_visible_width(line) for line in cell.splitlines()), default=0))
                
    return widths


def _pad_row(row, padding):
    """Add padding to each cell in a row."""
    pad_str = " " * padding
    return [f"{pad_str}{cell}{pad_str}" for cell in row]


def _build_line(widths, linefmt):
    """Build a separator line."""
    if not linefmt:
        return None
    cells = [linefmt.hline * w for w in widths]
    return linefmt.begin + linefmt.sep.join(cells) + linefmt.end


def _build_row(cells, widths, aligns, rowfmt):
    """Build a data or header row."""
    aligned_cells = []
    for cell, width, align in zip(cells, widths, aligns):
        if align == "decimal":
            # Simplified decimal alignment: right-align numbers, left-align others
            if _is_number(cell.strip()):
                aligned_cells.append(_align_string(cell, width, "right"))
            else:
                aligned_cells.append(_align_string(cell, width, "left"))
        else:
            aligned_cells.append(_align_string(cell, width, align))
    
    return rowfmt.begin + rowfmt.sep.join(aligned_cells) + rowfmt.end


def _render_multiline_row(row, col_widths, aligns, fmt):
    """Render a row that may contain multiline cells."""
    cell_lines = [cell.splitlines() or [""] for cell in row]
    max_lines = max(len(lines) for lines in cell_lines)
    
    for lines in cell_lines:
        lines.extend([""] * (max_lines - len(lines)))
        
    output_lines = []
    for i in range(max_lines):
        line_cells = [lines[i] for lines in cell_lines]
        padded_cells = _pad_row(line_cells, fmt.padding)
        padded_widths = [w + 2 * fmt.padding for w in col_widths]
        output_lines.append(_build_row(padded_cells, padded_widths, aligns, fmt.datarow))
        
    return output_lines


def tabulate(
    tabular_data,
    headers=(),
    tablefmt="simple",
    floatfmt="g",
    numalign="decimal",
    stralign="left",
    missingval="",
    showindex="default",
    disable_numparse=False,
    colalign=None,
):
    """Format a table."""
    if tabular_data is None:
        return ""

    # 1. Normalize data
    headers, data = _normalize_tabular_data(tabular_data, headers, showindex)
    
    # 2. Process data
    string_headers, string_rows, aligns = _process_data(
        headers, data, colalign, numalign, stralign, floatfmt, missingval
    )

    # 3. Calculate column widths
    col_widths = _get_column_widths(string_headers, string_rows)

    # 4. Get table format
    if isinstance(tablefmt, str):
        if tablefmt not in _table_formats:
            raise ValueError(f"Unknown table format: {tablefmt}")
        fmt = _table_formats[tablefmt]
    else:
        fmt = tablefmt

    # 5. Build the table string
    lines = []
    has_header = bool(string_headers)
    
    if not has_header and fmt.with_header_hide:
        hidden = fmt.with_header_hide
        fmt = fmt._replace(
            lineabove=None if "lineabove" in hidden else fmt.lineabove,
            linebelowheader=None if "linebelowheader" in hidden else fmt.linebelowheader,
            linebelow=None if "linebelow" in hidden else fmt.linebelow,
        )

    padded_widths = [w + 2 * fmt.padding for w in col_widths]

    if fmt.lineabove:
        lines.append(_build_line(padded_widths, fmt.lineabove))

    if has_header:
        padded_headers = _pad_row(string_headers, fmt.padding)
        lines.append(_build_row(padded_headers, padded_widths, aligns, fmt.headerrow))
        
        if fmt.linebelowheader:
            if tablefmt in ["pipe", "github", "markdown"]:
                sep_cells = []
                for i, align in enumerate(aligns):
                    w = col_widths[i]
                    if align == "right":
                        s = "-" * (w + fmt.padding) + ":"
                    elif align == "center":
                        s = ":" + "-" * (w) + ":"
                    else:
                        s = "-" * (w + fmt.padding + 1)
                    sep_cells.append(s)
                lines.append(fmt.linebelowheader.begin + fmt.linebelowheader.sep.join(sep_cells) + fmt.linebelowheader.end)
            else:
                lines.append(_build_line(padded_widths, fmt.linebelowheader))

    for i, row in enumerate(string_rows):
        lines.extend(_render_multiline_row(row, col_widths, aligns, fmt))
        if fmt.linebetweenrows and i < len(string_rows) - 1:
            lines.append(_build_line(padded_widths, fmt.linebetweenrows))

    if fmt.linebelow:
        lines.append(_build_line(padded_widths, fmt.linebelow))
        
    return "\n".join(filter(lambda x: x is not None, lines))
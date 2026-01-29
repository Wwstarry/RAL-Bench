"""
This module defines the various table format dictionaries and functions for
drawing a table. Each format dictionary is expected to have a draw() function or
logic that can be invoked to produce the final table output lines.
"""

def draw_plain(headers, rows, col_widths):
    """
    Plain table has no borders, just rows of data separated by spaces (or the minimal needed).
    We'll join columns with a single space, but preserve multiline cells.
    """
    lines = []
    # print header row
    header_block = row_to_lines(headers)
    for row_segment in header_block:
        lines.append(" ".join(row_segment))

    # print data row
    for row in rows:
        row_block = row_to_lines(row)
        for seg in row_block:
            lines.append(" ".join(seg))

    return lines

def draw_grid(headers, rows, col_widths):
    """
    Grid table uses a plus-dash-plus style box around each cell.
    We'll handle multiline by splitting each row into line segments,
    and reproducing the top/bottom edges as we go.
    """
    lines = []
    # separator line
    sep = create_grid_sep(col_widths)
    # top border
    lines.append(sep)
    # header
    header_block = row_to_lines(headers)
    for seg in header_block:
        row_text = []
        for i, cell in enumerate(seg):
            row_text.append("| " + cell + " ")
        row_text.append("|")
        lines.append("".join(row_text))
    # separator
    lines.append(sep)
    # rows
    for row in rows:
        row_block = row_to_lines(row)
        for seg in row_block:
            row_text = []
            for i, cell in enumerate(seg):
                row_text.append("| " + cell + " ")
            row_text.append("|")
            lines.append("".join(row_text))
        lines.append(sep)
    return lines

def draw_pipe(headers, rows, col_widths):
    """
    Pipe table is similar to GitHub markdown style:
    | col1 | col2 |
    With a header separator row.
    """
    lines = []
    # header
    header_block = row_to_lines(headers)
    # separator line after header
    pipe_sep = create_pipe_sep(col_widths)

    for seg_idx, seg in enumerate(header_block):
        row_text = []
        for i, cell in enumerate(seg):
            row_text.append("| " + cell + " ")
        row_text.append("|")
        lines.append("".join(row_text))
    lines.append(pipe_sep)

    # rows
    for row in rows:
        row_block = row_to_lines(row)
        for seg in row_block:
            row_text = []
            for i, cell in enumerate(seg):
                row_text.append("| " + cell + " ")
            row_text.append("|")
            lines.append("".join(row_text))
    return lines

def draw_html_like(headers, rows, col_widths):
    """
    Produce an HTML-ish table representation (not fully valid HTML, but somewhat close).
    We'll just show <table>, <tr>, <th> or <td>.
    """
    lines = []
    lines.append("<table>")
    # header
    header_block = row_to_lines(headers)
    if header_block:
        lines.append("  <tr>")
        # we only consider the first line of each multiline cell as the main line
        # for actual HTML, you'd do something more elaborate.
        for i, cell in enumerate(header_block[0]):
            lines.append(f"    <th>{cell}</th>")
        lines.append("  </tr>")

    # rows
    for row in rows:
        row_block = row_to_lines(row)
        for seg_idx, seg in enumerate(row_block):
            lines.append("  <tr>")
            for i, cell in enumerate(seg):
                lines.append(f"    <td>{cell}</td>")
            lines.append("  </tr>")
    lines.append("</table>")
    return lines

def draw_separated(headers, rows, col_widths, sep):
    """
    Use the given separator between columns, no borders. Each cell is inlined,
    multiline cells yield multiple lines. 
    """
    lines = []
    # header
    header_block = row_to_lines(headers)
    for row_seg in header_block:
        lines.append(sep.join(row_seg))
    # rows
    for row in rows:
        row_block = row_to_lines(row)
        for seg in row_block:
            lines.append(sep.join(seg))
    return lines

def row_to_lines(row_cells):
    """
    row_cells is a list of multiline strings (already aligned).
    Convert it into a list of "segments", where each segment is the i-th line
    of each cell.
    E.g. if cell1 has 2 lines, cell2 has 3 lines, we produce 3 segments,
    with empty lines for cell1 in segment 3, etc.
    """
    # row_cells is something like ["line1\nline2", "row2 single", ...]
    lines_per_cell = []
    max_lines = 0
    for c in row_cells:
        splitted = c.split('\n')
        lines_per_cell.append(splitted)
        if len(splitted) > max_lines:
            max_lines = len(splitted)

    segments = []
    for line_index in range(max_lines):
        seg = []
        for splitted in lines_per_cell:
            if line_index < len(splitted):
                seg.append(splitted[line_index])
            else:
                seg.append("")  # empty line if cell doesn't have that many lines
        segments.append(seg)
    return segments

def create_grid_sep(col_widths):
    """
    For 'grid' style, produce something like: +-----+---+-----+
    """
    parts = ["+" + "-" * (w + 2) for w in col_widths]
    return "".join(parts) + "+"

def create_pipe_sep(col_widths):
    """
    For 'pipe' style, produce something like: |-----|-----|
    """
    parts = []
    for w in col_widths:
        parts.append("|" + "-" * (w + 2))
    parts.append("|")
    return "".join(parts)

def make_separated_format_dict(separator):
    """
    Return a dictionary for a separated format that can be used by tabulate.
    """
    return {
        'draw': lambda headers, rows, widths: draw_separated(headers, rows, widths, separator)
    }

# Preset dictionaries for direct usage
PLAIN = {
    'draw': draw_plain
}
GRID = {
    'draw': draw_grid
}
PIPE = {
    'draw': draw_pipe
}
HTML = {
    'draw': draw_html_like
}

# For convenience: tsv, csv, etc.
SIMPLE_SEPARATED = {
    'tsv': "\t",
    'csv': ",",
}
import re
from collections import OrderedDict

def _is_sequence(obj):
    # str is sequence but we don't want to treat it as such here
    return (hasattr(obj, "__iter__") or hasattr(obj, "__getitem__")) and not isinstance(obj, (str, bytes, dict))

def _stringify(value):
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, complex)):
        return str(value)
    if isinstance(value, (list, tuple)):
        # Join multiline with \n
        return "\n".join(str(v) for v in value)
    return str(value)

def _split_multiline(cell):
    # Split cell content into lines, preserving empty lines
    if cell is None:
        return [""]
    if isinstance(cell, str):
        return cell.splitlines() or [""]
    return str(cell).splitlines() or [""]

def _normalize_tabular_data(tabular_data, headers):
    """
    Normalize input data into a list of lists and headers list.
    Supports:
    - list of lists
    - list of dicts
    - dict (single row)
    """
    if headers is None:
        # Try to infer headers if data is list of dicts or dict
        if isinstance(tabular_data, dict):
            headers = list(tabular_data.keys())
            rows = [[tabular_data.get(h, "") for h in headers]]
            return headers, rows
        elif _is_sequence(tabular_data) and len(tabular_data) > 0:
            first = tabular_data[0]
            if isinstance(first, dict):
                headers = list(OrderedDict.fromkeys(k for d in tabular_data for k in d.keys()))
                rows = []
                for d in tabular_data:
                    row = [d.get(h, "") for h in headers]
                    rows.append(row)
                return headers, rows
            elif _is_sequence(first):
                # list of lists, no headers
                return None, tabular_data
            else:
                # list of scalars
                return None, [[v] for v in tabular_data]
        else:
            # scalar or empty
            return None, [[tabular_data]]
    else:
        # headers given
        if isinstance(tabular_data, dict):
            # dict with headers: treat as single row
            rows = [[tabular_data.get(h, "") for h in headers]]
            return headers, rows
        elif _is_sequence(tabular_data):
            # list of lists or list of dicts
            if len(tabular_data) == 0:
                return headers, []
            first = tabular_data[0]
            if isinstance(first, dict):
                rows = []
                for d in tabular_data:
                    row = [d.get(h, "") for h in headers]
                    rows.append(row)
                return headers, rows
            elif _is_sequence(first):
                # list of lists
                return headers, tabular_data
            else:
                # list of scalars
                return headers, [[v] for v in tabular_data]
        else:
            # scalar with headers
            return headers, [[tabular_data]]

def _column_widths(table, headers, colalign):
    """
    Calculate max width of each column considering multiline cells.
    """
    ncols = len(table[0]) if table else (len(headers) if headers else 0)
    widths = [0] * ncols

    # Consider headers
    if headers:
        for i, h in enumerate(headers):
            lines = _split_multiline(_stringify(h))
            maxw = max(len(line) for line in lines)
            if maxw > widths[i]:
                widths[i] = maxw

    # Consider table cells
    for row in table:
        for i, cell in enumerate(row):
            lines = _split_multiline(_stringify(cell))
            maxw = max(len(line) for line in lines)
            if maxw > widths[i]:
                widths[i] = maxw

    # Ensure at least 1 width
    widths = [max(w, 1) for w in widths]

    # Adjust alignment: if colalign is given, ensure it matches ncols
    if colalign:
        if len(colalign) < ncols:
            colalign = list(colalign) + ["left"] * (ncols - len(colalign))
    else:
        colalign = ["left"] * ncols

    return widths, colalign

def _pad_cell_lines(lines, width, align):
    """
    Pad each line of a cell to width with alignment.
    """
    padded = []
    for line in lines:
        pad_len = width - len(line)
        if align == "right":
            padded.append(" " * pad_len + line)
        elif align == "center":
            left = pad_len // 2
            right = pad_len - left
            padded.append(" " * left + line + " " * right)
        else:
            # left
            padded.append(line + " " * pad_len)
    return padded

def _expand_rows(table):
    """
    Expand rows with multiline cells into multiple rows.
    Returns list of rows where each row is a list of strings.
    """
    expanded = []
    for row in table:
        # Split each cell into lines
        split_cells = [_split_multiline(_stringify(cell)) for cell in row]
        max_lines = max(len(lines) for lines in split_cells)
        # Pad each cell lines to max_lines with empty strings
        padded_cells = [lines + [""] * (max_lines - len(lines)) for lines in split_cells]
        # Build rows line by line
        for i in range(max_lines):
            expanded.append([padded_cells[col][i] for col in range(len(row))])
    return expanded

def simple_separated_format(table, headers=None, sep=" ", padding=1, colalign=None):
    """
    Format table with a simple separator (like CSV, TSV, or space).
    """
    headers, table = _normalize_tabular_data(table, headers)
    if not table and not headers:
        return ""

    widths, colalign = _column_widths(table, headers, colalign)

    pad = " " * padding
    sep_str = sep

    def format_row(row):
        cells = []
        for i, cell in enumerate(row):
            lines = _split_multiline(_stringify(cell))
            # For simple separated format, multiline cells are joined with space
            cell_text = " ".join(lines)
            align = colalign[i] if i < len(colalign) else "left"
            if align == "right":
                cell_text = cell_text.rjust(widths[i])
            elif align == "center":
                cell_text = cell_text.center(widths[i])
            else:
                cell_text = cell_text.ljust(widths[i])
            cells.append(cell_text)
        return sep_str.join(cells)

    lines = []
    if headers:
        lines.append(format_row(headers))
    for row in table:
        lines.append(format_row(row))
    return ("\n").join(lines)

def _build_border(left, mid, right, fill, widths):
    parts = [left]
    for i, w in enumerate(widths):
        parts.append(fill * (w + 2))
        if i < len(widths) - 1:
            parts.append(mid)
    parts.append(right)
    return "".join(parts)

def _format_grid(table, headers=None, colalign=None):
    headers, table = _normalize_tabular_data(table, headers)
    if not table and not headers:
        return ""

    widths, colalign = _column_widths(table, headers, colalign)

    # Prepare horizontal borders
    top_border = _build_border("┌", "┬", "┐", "─", widths)
    header_sep = _build_border("├", "┼", "┤", "─", widths)
    bottom_border = _build_border("└", "┴", "┘", "─", widths)

    # Expand rows for multiline cells
    expanded_table = _expand_rows(table)
    expanded_headers = _expand_rows([headers]) if headers else []

    lines = [top_border]

    # Format headers
    if headers:
        for hrow in expanded_headers:
            padded_cells = []
            for i, cell in enumerate(hrow):
                align = colalign[i] if i < len(colalign) else "left"
                padded = _pad_cell_lines([cell], widths[i], align)[0]
                padded_cells.append(padded)
            line = "│ " + " │ ".join(padded_cells) + " │"
            lines.append(line)
        lines.append(header_sep)

    # Format table rows
    # We need to group expanded rows back into original rows by multiline count
    # But for grid, we just print expanded rows sequentially
    for row in expanded_table:
        padded_cells = []
        for i, cell in enumerate(row):
            align = colalign[i] if i < len(colalign) else "left"
            padded = _pad_cell_lines([cell], widths[i], align)[0]
            padded_cells.append(padded)
        line = "│ " + " │ ".join(padded_cells) + " │"
        lines.append(line)

    lines.append(bottom_border)
    return "\n".join(lines)

def _format_plain(table, headers=None, colalign=None):
    headers, table = _normalize_tabular_data(table, headers)
    if not table and not headers:
        return ""

    widths, colalign = _column_widths(table, headers, colalign)

    expanded_table = _expand_rows(table)
    expanded_headers = _expand_rows([headers]) if headers else []

    lines = []

    if headers:
        for hrow in expanded_headers:
            padded_cells = []
            for i, cell in enumerate(hrow):
                align = colalign[i] if i < len(colalign) else "left"
                padded = _pad_cell_lines([cell], widths[i], align)[0]
                padded_cells.append(padded)
            lines.append(" ".join(padded_cells))

    for row in expanded_table:
        padded_cells = []
        for i, cell in enumerate(row):
            align = colalign[i] if i < len(colalign) else "left"
            padded = _pad_cell_lines([cell], widths[i], align)[0]
            padded_cells.append(padded)
        lines.append(" ".join(padded_cells))

    return "\n".join(lines)

def _format_pipe(table, headers=None, colalign=None):
    headers, table = _normalize_tabular_data(table, headers)
    if not table and not headers:
        return ""

    widths, colalign = _column_widths(table, headers, colalign)

    expanded_table = _expand_rows(table)
    expanded_headers = _expand_rows([headers]) if headers else []

    lines = []

    def format_row(row):
        padded_cells = []
        for i, cell in enumerate(row):
            align = colalign[i] if i < len(colalign) else "left"
            padded = _pad_cell_lines([cell], widths[i], align)[0]
            padded_cells.append(padded)
        return "| " + " | ".join(padded_cells) + " |"

    if headers:
        for hrow in expanded_headers:
            lines.append(format_row(hrow))
        # separator line
        sep_cells = []
        for i, w in enumerate(widths):
            align = colalign[i] if i < len(colalign) else "left"
            if align == "right":
                sep_cells.append("-" * (w - 1) + ":")
            elif align == "center":
                sep_cells.append(":" + "-" * (w - 2) + ":")
            else:
                sep_cells.append(":" + "-" * (w - 1))
        lines.append("| " + " | ".join(sep_cells) + " |")

    for row in expanded_table:
        lines.append(format_row(row))

    return "\n".join(lines)

def _format_html(table, headers=None, colalign=None):
    headers, table = _normalize_tabular_data(table, headers)
    if not table and not headers:
        return ""

    widths, colalign = _column_widths(table, headers, colalign)

    expanded_table = _expand_rows(table)
    expanded_headers = _expand_rows([headers]) if headers else []

    def escape_html(text):
        text = text.replace("&", "&amp;")
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
        text = text.replace('"', "&quot;")
        return text

    lines = []
    lines.append("<table>")

    if headers:
        lines.append("  <thead>")
        for hrow in expanded_headers:
            lines.append("    <tr>")
            for i, cell in enumerate(hrow):
                align = colalign[i] if i < len(colalign) else "left"
                style = f' style="text-align: {align};"' if align else ""
                lines.append(f"      <th{style}>{escape_html(cell)}</th>")
            lines.append("    </tr>")
        lines.append("  </thead>")

    lines.append("  <tbody>")
    for row in expanded_table:
        lines.append("    <tr>")
        for i, cell in enumerate(row):
            align = colalign[i] if i < len(colalign) else "left"
            style = f' style="text-align: {align};"' if align else ""
            lines.append(f"      <td{style}>{escape_html(cell)}</td>")
        lines.append("    </tr>")
    lines.append("  </tbody>")
    lines.append("</table>")
    return "\n".join(lines)

def _format_tsv(table, headers=None, colalign=None):
    return simple_separated_format(table, headers, sep="\t", padding=0, colalign=colalign)

def _format_csv(table, headers=None, colalign=None):
    # CSV with comma separator, quote cells if needed
    headers, table = _normalize_tabular_data(table, headers)
    if not table and not headers:
        return ""

    def quote_cell(cell):
        s = _stringify(cell)
        if any(c in s for c in ('"', ",", "\n", "\r")):
            s = s.replace('"', '""')
            return f'"{s}"'
        return s

    lines = []
    if headers:
        lines.append(",".join(quote_cell(h) for h in headers))
    for row in table:
        lines.append(",".join(quote_cell(c) for c in row))
    return "\n".join(lines)

_table_formats = {
    "plain": _format_plain,
    "grid": _format_grid,
    "pipe": _format_pipe,
    "html": _format_html,
    "tsv": _format_tsv,
    "csv": _format_csv,
}

def tabulate(tabular_data, headers=None, tablefmt="simple", colalign=None):
    """
    Format tabular data (list of lists, list of dicts, dict) into a string table.

    Parameters:
    - tabular_data: data to format
    - headers: list of headers or None
    - tablefmt: format name or callable
    - colalign: list of alignments per column ("left", "right", "center")

    Returns:
    - formatted string
    """
    if callable(tablefmt):
        return tablefmt(tabular_data, headers=headers, colalign=colalign)
    fmt = tablefmt.lower()
    if fmt == "simple":
        fmt = "plain"
    if fmt not in _table_formats:
        raise ValueError(f"Unknown table format: {tablefmt}")
    formatter = _table_formats[fmt]
    return formatter(tabular_data, headers=headers, colalign=colalign)
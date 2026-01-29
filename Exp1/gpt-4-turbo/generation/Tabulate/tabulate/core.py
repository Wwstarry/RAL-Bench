import collections.abc
import numbers
from .formats import TABLE_FORMATS, simple_separated_format

def tabulate(tabular_data, headers=(), tablefmt="simple", stralign="left", numalign="decimal", floatfmt="g", missingval="", showindex="default", disable_numparse=False):
    """
    Format tabular data.

    Args:
        tabular_data: list of lists, list of dicts, dict of iterables, etc.
        headers: list of header names, or "keys", or "firstrow", or empty.
        tablefmt: name of table format.
        stralign: alignment for strings ("left", "center", "right").
        numalign: alignment for numbers ("right", "center", "left", "decimal").
        floatfmt: format string for floats.
        missingval: value to replace missing cells.
        showindex: "default", "always", "never", or bool.
        disable_numparse: if True, don't try to parse numbers.

    Returns:
        str: formatted table.
    """
    rows, header_row = _normalize_data(tabular_data, headers, missingval)
    if showindex == "always" or (showindex == "default" and _should_show_index(tabular_data, headers)):
        rows = [[i] + list(row) for i, row in enumerate(rows)]
        if header_row:
            header_row = [""] + list(header_row)
    elif showindex == "never" or showindex is False:
        pass
    elif showindex is True:
        rows = [[i] + list(row) for i, row in enumerate(rows)]
        if header_row:
            header_row = [""] + list(header_row)
    # else: default behavior

    # Parse numbers unless disabled
    if not disable_numparse:
        rows = [_parse_row(row) for row in rows]
        if header_row:
            header_row = list(header_row)

    # Calculate column widths
    all_rows = []
    if header_row:
        all_rows.append(header_row)
    all_rows.extend(rows)
    col_widths = _calc_col_widths(all_rows, floatfmt, missingval)

    # Alignment
    aligns = _get_aligns(header_row, rows, stralign, numalign)

    # Format cells
    formatted_rows = []
    for row in rows:
        formatted_rows.append(_format_row(row, col_widths, aligns, floatfmt, missingval))

    if header_row:
        formatted_header = _format_row(header_row, col_widths, aligns, floatfmt, missingval)
    else:
        formatted_header = None

    # Get format
    fmt = TABLE_FORMATS.get(tablefmt, TABLE_FORMATS["simple"])
    return fmt(formatted_rows, formatted_header, col_widths)

def _normalize_data(tabular_data, headers, missingval):
    # Accepts list of lists, list of dicts, dict of iterables, etc.
    # Returns (rows, header_row)
    if isinstance(tabular_data, dict):
        # Dict of columns
        keys = list(tabular_data.keys())
        columns = [list(tabular_data[k]) for k in keys]
        nrows = max(len(col) for col in columns)
        rows = []
        for i in range(nrows):
            row = []
            for col in columns:
                if i < len(col):
                    row.append(col[i])
                else:
                    row.append(missingval)
            rows.append(row)
        header_row = keys if headers in ("keys", True) or headers == () else headers
        return rows, header_row
    elif isinstance(tabular_data, collections.abc.Mapping):
        # Mapping (dict-like)
        keys = list(tabular_data.keys())
        columns = [list(tabular_data[k]) for k in keys]
        nrows = max(len(col) for col in columns)
        rows = []
        for i in range(nrows):
            row = []
            for col in columns:
                if i < len(col):
                    row.append(col[i])
                else:
                    row.append(missingval)
            rows.append(row)
        header_row = keys if headers in ("keys", True) or headers == () else headers
        return rows, header_row
    elif isinstance(tabular_data, list) and tabular_data and isinstance(tabular_data[0], dict):
        # List of dicts
        all_keys = set()
        for d in tabular_data:
            all_keys.update(d.keys())
        keys = list(all_keys)
        rows = []
        for d in tabular_data:
            row = [d.get(k, missingval) for k in keys]
            rows.append(row)
        header_row = keys if headers in ("keys", True) or headers == () else headers
        return rows, header_row
    elif isinstance(tabular_data, list) and tabular_data and isinstance(tabular_data[0], (list, tuple)):
        # List of lists
        rows = [list(row) for row in tabular_data]
        if headers == "firstrow":
            header_row = rows[0]
            rows = rows[1:]
        elif headers and headers != ():
            header_row = list(headers)
        else:
            header_row = None
        return rows, header_row
    elif isinstance(tabular_data, list) and tabular_data and isinstance(tabular_data[0], str):
        # List of strings
        rows = [[cell] for cell in tabular_data]
        header_row = headers if headers else None
        return rows, header_row
    elif isinstance(tabular_data, list):
        # List of scalars
        rows = [[cell] for cell in tabular_data]
        header_row = headers if headers else None
        return rows, header_row
    else:
        # Fallback: try to treat as iterable of iterables
        try:
            rows = [list(row) for row in tabular_data]
            if headers == "firstrow":
                header_row = rows[0]
                rows = rows[1:]
            elif headers and headers != ():
                header_row = list(headers)
            else:
                header_row = None
            return rows, header_row
        except Exception:
            raise ValueError("Unsupported tabular_data type")

def _should_show_index(tabular_data, headers):
    # Show index for dict of columns, not for list of lists/dicts
    if isinstance(tabular_data, dict):
        return True
    return False

def _parse_row(row):
    # Try to parse numbers for alignment
    parsed = []
    for cell in row:
        if isinstance(cell, str):
            try:
                if "." in cell:
                    parsed.append(float(cell))
                else:
                    parsed.append(int(cell))
            except Exception:
                parsed.append(cell)
        else:
            parsed.append(cell)
    return parsed

def _calc_col_widths(rows, floatfmt, missingval):
    # Returns list of max widths per column, considering multiline cells
    ncols = max(len(row) for row in rows)
    col_widths = [0] * ncols
    for row in rows:
        for i, cell in enumerate(row):
            cell_str = _cell_to_str(cell, floatfmt, missingval)
            lines = cell_str.splitlines() or [""]
            maxlen = max(len(line) for line in lines)
            if maxlen > col_widths[i]:
                col_widths[i] = maxlen
    return col_widths

def _cell_to_str(cell, floatfmt, missingval):
    if cell is None or cell == "":
        return str(missingval)
    if isinstance(cell, float):
        return format(cell, floatfmt)
    return str(cell)

def _get_aligns(header_row, rows, stralign, numalign):
    # Returns list of alignments per column
    ncols = max(len(row) for row in ([header_row] if header_row else []) + rows)
    aligns = []
    for col in range(ncols):
        # Check if column is numeric
        is_numeric = True
        for row in rows:
            if col >= len(row):
                continue
            val = row[col]
            if not isinstance(val, numbers.Number):
                is_numeric = False
                break
        if is_numeric:
            aligns.append(numalign)
        else:
            aligns.append(stralign)
    return aligns

def _format_row(row, col_widths, aligns, floatfmt, missingval):
    # Format each cell, pad, align, handle multiline
    formatted_cells = []
    for i, cell in enumerate(row):
        cell_str = _cell_to_str(cell, floatfmt, missingval)
        lines = cell_str.splitlines() or [""]
        width = col_widths[i]
        align = aligns[i] if i < len(aligns) else "left"
        formatted_lines = [_pad_line(line, width, align) for line in lines]
        formatted_cell = "\n".join(formatted_lines)
        formatted_cells.append(formatted_cell)
    return formatted_cells

def _pad_line(line, width, align):
    if align == "right":
        return line.rjust(width)
    elif align == "center":
        return line.center(width)
    elif align == "decimal":
        # Align at decimal point
        if "." in line:
            left, right = line.split(".", 1)
            pad_left = width - len(line)
            return " " * pad_left + line
        else:
            return line.rjust(width)
    else:
        return line.ljust(width)
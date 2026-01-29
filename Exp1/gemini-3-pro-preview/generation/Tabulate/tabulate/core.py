import math
from .formats import _formats, Line, DataRow, TableFormat

_DEFAULT_FLOATFMT = "g"
_DEFAULT_MISSINGVAL = ""


def simple_separated_format(separator):
    """Construct a simple TableFormat with a specific separator."""
    return TableFormat(
        None, None, None, None,
        DataRow("", separator, ""),
        DataRow("", separator, ""),
        0, None
    )


def _is_number(x):
    if x is None:
        return False
    if isinstance(x, (int, float)):
        return True
    if isinstance(x, str):
        # Basic check for string-formatted numbers
        try:
            float(x)
            return True
        except ValueError:
            return False
    return False


def _format_number(val, floatfmt):
    if val is None:
        return ""
    if isinstance(val, float):
        return format(val, floatfmt)
    return str(val)


def _align_cell(content, width, alignment, padding_char=" "):
    if alignment == "right":
        return content.rjust(width, padding_char)
    elif alignment == "center":
        return content.center(width, padding_char)
    else:  # left or default
        return content.ljust(width, padding_char)


def _normalize_tabular_data(data, headers, showindex="default"):
    """
    Transform input data (list of lists, dict of lists, list of dicts)
    into a consistent list of rows (list of lists) and a list of headers.
    """
    rows = []
    header_row = []

    # 1. Handle Dictionary of Iterables (Columns)
    if isinstance(data, dict):
        # keys are headers, values are columns
        if not headers or headers == "keys":
            header_row = list(data.keys())
        else:
            header_row = headers
        
        cols = list(data.values())
        # Transpose columns to rows
        if cols:
            max_len = max(len(c) for c in cols)
            for i in range(max_len):
                row = []
                for col in cols:
                    row.append(col[i] if i < len(col) else None)
                rows.append(row)

    # 2. Handle List of Dictionaries
    elif isinstance(data, list) and data and isinstance(data[0], dict):
        keys = set()
        for d in data:
            keys.update(d.keys())
        # Sort keys to ensure deterministic order if not provided
        sorted_keys = sorted(list(keys))
        
        if not headers or headers == "keys":
            header_row = sorted_keys
        elif isinstance(headers, list):
            header_row = headers
        
        # If headers provided, use that order, otherwise use sorted keys
        lookup_keys = header_row if (headers and headers != "firstrow") else sorted_keys

        for d in data:
            row = [d.get(k) for k in lookup_keys]
            rows.append(row)

    # 3. Handle Iterable of Iterables (List of Lists)
    else:
        # Convert to list of lists
        rows = [list(row) for row in data]
        
        if headers == "firstrow" and rows:
            header_row = rows[0]
            rows = rows[1:]
        elif isinstance(headers, list):
            header_row = headers

    # Handle showindex
    if showindex == "always" or (showindex == "default" and isinstance(data, dict)):
        # Logic for index generation could be complex, simplified here
        pass 
    elif isinstance(showindex, (list, tuple, range)):
        # Prepend index column
        for i, row in enumerate(rows):
            idx_val = showindex[i] if i < len(showindex) else ""
            row.insert(0, idx_val)
        if header_row:
            header_row.insert(0, "")
    elif showindex:
        # Boolean true, use row numbers
        for i, row in enumerate(rows):
            row.insert(0, i)
        if header_row:
            header_row.insert(0, "")

    return rows, header_row


def tabulate(tabular_data, headers=(), tablefmt="simple", floatfmt=_DEFAULT_FLOATFMT, 
             numalign="default", stralign="default", missingval=_DEFAULT_MISSINGVAL, 
             showindex="default", disable_numparse=False, colalign=None):
    
    # 1. Normalize Data
    rows, header_row = _normalize_tabular_data(tabular_data, headers, showindex)

    if not rows and not header_row:
        return ""

    # 2. Resolve Table Format
    if isinstance(tablefmt, TableFormat):
        fmt = tablefmt
    elif tablefmt in _formats:
        fmt = _formats[tablefmt]
    else:
        raise ValueError(f"Unknown table format: {tablefmt}")

    # 3. Determine Column Types and Alignments
    # Transpose to check columns
    num_cols = 0
    if rows:
        num_cols = max(len(r) for r in rows)
    if header_row:
        num_cols = max(num_cols, len(header_row))

    # Pad rows to ensure rectangular shape
    for row in rows:
        while len(row) < num_cols:
            row.append(None)
    
    col_types = ["str"] * num_cols
    
    if not disable_numparse:
        for c in range(num_cols):
            is_numeric = True
            for r in rows:
                val = r[c]
                if val is not None and val != missingval and not _is_number(val):
                    is_numeric = False
                    break
            if is_numeric and rows: # If rows is empty, default to str
                col_types[c] = "num"

    # Resolve alignments
    # Priority: colalign arg > type-based default
    final_colalign = []
    if colalign:
        final_colalign = list(colalign)
        while len(final_colalign) < num_cols:
            final_colalign.append("left") # Fallback
    else:
        for c in range(num_cols):
            if col_types[c] == "num":
                final_colalign.append("right" if numalign == "default" else numalign)
            else:
                final_colalign.append("left" if stralign == "default" else stralign)

    # 4. Format Data as Strings
    formatted_rows = []
    for row in rows:
        new_row = []
        for c, val in enumerate(row):
            if val is None:
                s = missingval
            elif col_types[c] == "num":
                s = _format_number(val, floatfmt)
            else:
                s = str(val)
            new_row.append(s)
        formatted_rows.append(new_row)
    
    formatted_headers = [str(h) for h in header_row]

    # 5. Calculate Column Widths
    # We must account for multiline cells
    col_widths = [0] * num_cols

    def update_widths(row_data):
        for c, cell in enumerate(row_data):
            if c < num_cols:
                # Split by newline to find max width of this cell
                lines = cell.split('\n')
                w = max(len(line) for line in lines) if lines else 0
                col_widths[c] = max(col_widths[c], w)

    if formatted_headers:
        update_widths(formatted_headers)
    for row in formatted_rows:
        update_widths(row)

    # 6. Render
    lines = []
    
    pad = " " * fmt.padding

    def build_row(cells, row_fmt):
        # Handle multiline cells by expanding into multiple physical lines
        # 1. Split all cells into lines
        cell_lines = [c.split('\n') for c in cells]
        height = max(len(cl) for cl in cell_lines) if cell_lines else 0
        
        physical_lines = []
        for h in range(height):
            line_parts = []
            if row_fmt.begin:
                line_parts.append(row_fmt.begin)
            
            for c in range(num_cols):
                # Get content for this height, or empty string
                content = cell_lines[c][h] if h < len(cell_lines[c]) else ""
                
                # Align
                aligned = _align_cell(content, col_widths[c], final_colalign[c])
                
                # Add padding
                # Special case: if no borders/separators, padding might differ, 
                # but standard tabulate applies padding around content inside the separator.
                # If padding is 0, we don't add spaces.
                if fmt.padding > 0:
                    cell_str = f"{pad}{aligned}{pad}"
                else:
                    cell_str = aligned
                
                line_parts.append(cell_str)
                
                if c < num_cols - 1:
                    line_parts.append(row_fmt.sep)
            
            if row_fmt.end:
                line_parts.append(row_fmt.end)
            
            physical_lines.append("".join(line_parts))
        
        return physical_lines

    def build_line(line_fmt):
        if not line_fmt:
            return None
        parts = []
        if line_fmt.begin:
            parts.append(line_fmt.begin)
        
        for c in range(num_cols):
            w = col_widths[c] + (2 * fmt.padding)
            parts.append(line_fmt.hline * w)
            if c < num_cols - 1:
                parts.append(line_fmt.sep)
        
        if line_fmt.end:
            parts.append(line_fmt.end)
        return "".join(parts)

    # -- Rendering Sequence --

    # Line Above
    if fmt.lineabove:
        l = build_line(fmt.lineabove)
        if l: lines.append(l)

    # Header
    if formatted_headers:
        header_lines = build_row(formatted_headers, fmt.headerrow)
        lines.extend(header_lines)
        
        if fmt.linebelowheader:
            l = build_line(fmt.linebelowheader)
            if l: lines.append(l)

    # Rows
    for i, row in enumerate(formatted_rows):
        # Line between rows
        if i > 0 and fmt.linebetweenrows:
            l = build_line(fmt.linebetweenrows)
            if l: lines.append(l)
            
        row_lines = build_row(row, fmt.datarow)
        lines.extend(row_lines)

    # Line Below
    if fmt.linebelow:
        l = build_line(fmt.linebelow)
        if l: lines.append(l)

    return "\n".join(lines)
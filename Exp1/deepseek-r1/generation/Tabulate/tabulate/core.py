from .formats import PRESET_FORMATS, TableFormat, simple_separated_format

def _normalize_table(table, headers):
    if not table:
        return [], []

    if isinstance(table[0], dict):
        if headers == "keys":
            headers = list(table[0].keys())
        rows = [[row.get(key, '') for key in headers] for row in table]
    else:
        rows = [list(row) for row in table]

    return headers, rows

def _calculate_widths(headers, rows):
    if not rows:
        return [len(str(h)) for h in headers] if headers else []

    widths = []
    num_columns = max(len(headers) if headers else 0, max(len(row) for row in rows))
    
    for i in range(num_columns):
        col_data = []
        if headers and i < len(headers):
            col_data.append(str(headers[i]))
        for row in rows:
            if i < len(row):
                cell = str(row[i])
                if '\n' in cell:
                    col_data.extend(cell.split('\n'))
                else:
                    col_data.append(cell)
        if col_data:
            col_width = max(len(item) for item in col_data)
            widths.append(col_width)
        else:
            widths.append(0)
    return widths

def _align_row(row, widths, align_funcs):
    aligned = []
    for i, (cell, width) in enumerate(zip(row, widths)):
        if i >= len(align_funcs):
            align_func = str.ljust
        else:
            align_func = align_funcs[i]
        cell_str = str(cell)
        if '\n' in cell_str:
            lines = cell_str.split('\n')
            aligned_lines = [align_func(line, width) for line in lines]
            aligned.append('\n'.join(aligned_lines))
        else:
            aligned.append(align_func(cell_str, width))
    return aligned

def tabulate(table, headers=None, tablefmt="plain", numalign="right", stralign="left"):
    if tablefmt in PRESET_FORMATS:
        fmt = PRESET_FORMATS[tablefmt]
    else:
        raise ValueError(f"Table format {tablefmt} not supported")

    headers, rows = _normalize_table(table, headers)
    if not rows:
        return ""

    widths = _calculate_widths(headers, rows)
    align_funcs = []
    for i in range(len(widths)):
        if headers and i < len(headers) and any(isinstance(row[i], (int, float)) for row in rows if i < len(row)):
            align = numalign
        else:
            align = stralign
        if align == "left":
            align_funcs.append(str.ljust)
        elif align == "right":
            align_funcs.append(str.rjust)
        elif align == "center":
            align_funcs.append(str.center)
        else:
            align_funcs.append(str.ljust)

    output_lines = []
    if fmt.lineabove and (headers or "lineabove" not in fmt.with_header_hide):
        output_lines.append(fmt.lineabove(widths))

    if headers:
        aligned_headers = _align_row(headers, widths, align_funcs)
        header_line = fmt.headerrow(aligned_headers, widths)
        output_lines.append(header_line)
        if fmt.linebelowheader and (headers or "linebelowheader" not in fmt.with_header_hide):
            output_lines.append(fmt.linebelowheader(widths))

    for i, row in enumerate(rows):
        if i > 0 and fmt.linebetweenrows:
            output_lines.append(fmt.linebetweenrows(widths))
        aligned_row = _align_row(row, widths, align_funcs)
        output_lines.append(fmt.datarow(aligned_row, widths))

    if fmt.linebelow and (headers or "linebelow" not in fmt.with_header_hide):
        output_lines.append(fmt.linebelow(widths))

    return '\n'.join(output_lines)
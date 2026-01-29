"""
Core functionality for tabulate - collecting rows, determining widths,
handling multiline cells, alignment, and dispatching to the chosen format.
"""

import math
import sys
from .formats import (
    PLAIN,
    GRID,
    PIPE,
    HTML,
    SIMPLE_SEPARATED,
    make_separated_format_dict,
)

def isnumber(value):
    """
    Check if a cell value is numeric.
    """
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False

def split_multiline(value):
    """
    Split a cell's string representation into multiple lines if needed.
    """
    return str(value).split('\n')

def get_headers_and_rows(tabular_data, headers=None):
    """
    From various structures (list of lists, list of dicts, single dict),
    produce headers and rows in a consistent list-of-lists form.
    """
    if not tabular_data:
        # no data
        return [], []

    # if it's a single dict, wrap it
    if isinstance(tabular_data, dict):
        tabular_data = [tabular_data]

    # if data is list of dicts
    if all(isinstance(r, dict) for r in tabular_data):
        # gather all columns from union of dictionaries
        all_keys = set()
        for d in tabular_data:
            all_keys.update(d.keys())
        all_keys = list(all_keys)

        if headers is None or not headers:
            headers = all_keys
        rows = []
        for d in tabular_data:
            row = [d.get(k, "") for k in headers]
            rows.append(row)
        return list(headers), rows
    else:
        # assume list of lists
        # use the length of the first row to define columns
        first_row = tabular_data[0]
        length = len(first_row)
        if headers is None or not headers:
            headers = list(range(length))
        rows = []
        for row in tabular_data:
            # in case of mismatch, pad or slice
            new_row = list(row[:length]) + [""] * (length - len(row))
            rows.append(new_row)
        return headers, rows

def compute_column_widths(headers, rows):
    """
    Compute the maximum width required for each column (considering multiline).
    Return a list of widths, one per column.
    """
    # all cells, including headers, can have multiple lines
    columns = len(headers)
    col_widths = [0] * columns

    # handle header widths
    for i in range(columns):
        lines = split_multiline(headers[i])
        max_len = max(len(line) for line in lines) if lines else 0
        if max_len > col_widths[i]:
            col_widths[i] = max_len

    # handle row widths
    for row in rows:
        for i, cell in enumerate(row):
            lines = split_multiline(cell)
            max_len = max(len(line) for line in lines) if lines else 0
            if max_len > col_widths[i]:
                col_widths[i] = max_len

    return col_widths

def align_cell(cell, width, is_numeric=False, alignment='left'):
    """
    Align a single cell (potentially multiline) to a given width.
    alignment can be 'left', 'right', or 'decimal' (treated as 'right' for simplicity).
    """
    lines = split_multiline(cell)

    # decimal alignment -> right align for simplicity
    if alignment == 'decimal':
        alignment = 'right'

    aligned_lines = []
    for line in lines:
        if alignment == 'right':
            aligned_lines.append(line.rjust(width))
        else:
            # default to left
            aligned_lines.append(line.ljust(width))
    # Re-join with newlines
    return '\n'.join(aligned_lines)

def tabulate(
    tabular_data,
    headers=None,
    tablefmt="plain",
    stralign="left",
    numalign="decimal",
    # optional extra placeholders:
    **kwargs
):
    """
    Format tabular data (list of lists or list of dicts) into a table.
    This function dispatches to different formatting approaches based on tablefmt.
    """
    # get the format dictionary (or generate it if it's a simple separated format)
    if tablefmt in [PLAIN, GRID, PIPE, HTML] or callable(tablefmt):
        format_dict = tablefmt if callable(tablefmt) else tablefmt
    elif isinstance(tablefmt, str) and tablefmt.startswith("simple-"):
        sep = tablefmt.replace("simple-", "")
        format_dict = make_separated_format_dict(sep)
    else:
        # attempt to see if it's a separated format
        if tablefmt in SIMPLE_SEPARATED:
            format_dict = make_separated_format_dict(SIMPLE_SEPARATED[tablefmt])
        else:
            # fallback to plain
            format_dict = PLAIN

    actual_format = format_dict

    # convert our data into consistent headers, rows
    headers, rows = get_headers_and_rows(tabular_data, headers)

    # compute column widths
    col_widths = compute_column_widths(headers, rows)
    # aligned table data (as multiline strings)
    aligned_headers = []
    for i, h in enumerate(headers):
        # if numeric?
        numeric = isnumber(h)
        alignment = numalign if numeric else stralign
        aligned_headers.append(align_cell(h, col_widths[i], numeric, alignment))

    aligned_rows = []
    for row in rows:
        newrow = []
        for i, cell in enumerate(row):
            numeric = isnumber(cell)
            alignment = numalign if numeric else stralign
            newrow.append(align_cell(cell, col_widths[i], numeric, alignment))
        aligned_rows.append(newrow)

    out = []
    # now pass this to the table drawing function in actual_format
    if callable(actual_format):
        out = actual_format(aligned_headers, aligned_rows, col_widths)
    elif isinstance(actual_format, dict) and 'draw' in actual_format:
        out = actual_format['draw'](aligned_headers, aligned_rows, col_widths)
    else:
        # fallback: plain
        out = PLAIN['draw'](aligned_headers, aligned_rows, col_widths)
    return "\n".join(out)

def simple_separated_format(separator):
    """
    Return a tablefmt that uses the given separator between cells with no edges.
    Example usage:
        tabulate(data, tablefmt=simple_separated_format(","))
    """
    return make_separated_format_dict(separator)
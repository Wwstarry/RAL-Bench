# tabulate/core.py

import math
from .formats import PRESET_FORMATS

def tabulate(data, headers=None, tablefmt="plain", numalign="right", stralign="left"):
    """
    Generate a formatted table string from the given data.

    :param data: List of lists, dictionaries, or list of dictionaries.
    :param headers: Optional list of column headers.
    :param tablefmt: Table format (e.g., "plain", "grid", "pipe").
    :param numalign: Alignment for numeric columns ("left", "center", "right").
    :param stralign: Alignment for string columns ("left", "center", "right").
    :return: Formatted table string.
    """
    if tablefmt not in PRESET_FORMATS:
        raise ValueError(f"Unknown table format: {tablefmt}")

    format_func = PRESET_FORMATS[tablefmt]
    rows = _normalize_data(data, headers)
    column_widths = _calculate_column_widths(rows)
    formatted_rows = _format_rows(rows, column_widths, numalign, stralign)
    return format_func(formatted_rows, column_widths)

def _normalize_data(data, headers):
    """
    Normalize data into a list of lists, handling dictionaries and headers.
    """
    if isinstance(data, dict):
        data = [data]
    if isinstance(data, list) and all(isinstance(row, dict) for row in data):
        keys = headers or sorted({key for row in data for key in row.keys()})
        rows = [[row.get(key, "") for key in keys] for row in data]
        return [keys] + rows
    if headers:
        return [headers] + data
    return data

def _calculate_column_widths(rows):
    """
    Calculate the maximum width of each column.
    """
    num_columns = max(len(row) for row in rows)
    column_widths = [0] * num_columns
    for row in rows:
        for i, cell in enumerate(row):
            column_widths[i] = max(column_widths[i], len(str(cell)))
    return column_widths

def _format_rows(rows, column_widths, numalign, stralign):
    """
    Format rows with alignment and padding.
    """
    def align_cell(cell, width, alignment):
        cell = str(cell)
        if alignment == "right":
            return cell.rjust(width)
        elif alignment == "center":
            return cell.center(width)
        else:
            return cell.ljust(width)

    formatted_rows = []
    for row in rows:
        formatted_row = [
            align_cell(cell, column_widths[i], numalign if isinstance(cell, (int, float)) else stralign)
            for i, cell in enumerate(row)
        ]
        formatted_rows.append(formatted_row)
    return formatted_rows
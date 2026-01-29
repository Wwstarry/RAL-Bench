import re
from itertools import chain
from typing import Any, Dict, Iterable, List, Optional, Sequence, Union

from .formats import _FORMAT_ALIASES, _TABLE_FORMATS

def _normalize_table(table: Any) -> List[List[str]]:
    """Convert various table formats into a list of lists of strings."""
    if not table:
        return []
    
    if isinstance(table, dict):
        headers = list(table.keys())
        rows = list(zip(*table.values()))
        return [headers] + list(rows)
    
    if isinstance(table[0], dict):
        headers = list(table[0].keys())
        rows = [[str(row.get(key, "")) for key in headers] for row in table]
        return [headers] + rows
    
    return [[str(cell) for cell in row] for row in table]

def _align_column(
    column: List[str], align: Optional[str], minwidth: int = 0
) -> List[str]:
    """Align all cells in a column according to the specified alignment."""
    if not column:
        return column
    
    if align is None:
        return column
    
    max_len = max(len(cell) for cell in column)
    max_len = max(max_len, minwidth)
    
    aligned = []
    for cell in column:
        if align == "left":
            aligned.append(cell.ljust(max_len))
        elif align == "right":
            aligned.append(cell.rjust(max_len))
        elif align == "center":
            aligned.append(cell.center(max_len))
        elif align == "decimal":
            parts = re.split(r"(\d+\.\d+)", cell)
            aligned.append(parts[0].ljust(max_len - len(parts[1])) + parts[1])
        else:
            aligned.append(cell)
    
    return aligned

def _calculate_column_widths(table: List[List[str]]) -> List[int]:
    """Calculate the maximum width for each column."""
    if not table:
        return []
    
    num_cols = max(len(row) for row in table) if table else 0
    widths = [0] * num_cols
    
    for row in table:
        for i, cell in enumerate(row):
            cell_lines = cell.split("\n")
            max_line_len = max(len(line) for line in cell_lines)
            widths[i] = max(widths[i], max_line_len)
    
    return widths

def _format_row(
    row: List[str],
    widths: List[int],
    aligns: Optional[List[str]],
    padding: int = 1,
    left_edge: str = "",
    separator: str = " ",
    right_edge: str = "",
) -> str:
    """Format a single row with given widths and alignment."""
    if not row:
        return left_edge + right_edge
    
    aligns = aligns or ["left"] * len(row)
    cells = []
    
    for cell, width, align in zip(row, widths, aligns):
        cell_lines = cell.split("\n")
        aligned_lines = _align_column(cell_lines, align, width)
        padded_lines = [
            " " * padding + line + " " * padding for line in aligned_lines
        ]
        cells.append(padded_lines)
    
    max_lines = max(len(cell) for cell in cells)
    formatted_lines = []
    
    for line_num in range(max_lines):
        line_parts = []
        for cell in cells:
            if line_num < len(cell):
                line_parts.append(cell[line_num])
            else:
                line_parts.append(" " * (widths[cells.index(cell)] + 2 * padding))
        
        line = left_edge + separator.join(line_parts) + right_edge
        formatted_lines.append(line)
    
    return "\n".join(formatted_lines)

def tabulate(
    table: Any,
    headers: Union[str, Sequence[str]] = (),
    tablefmt: str = "plain",
    showindex: bool = False,
    align: Union[str, Sequence[str], None] = None,
    floatfmt: str = "g",
    numalign: str = "decimal",
    stralign: str = "left",
) -> str:
    """Format a table into various output formats."""
    normalized = _normalize_table(table)
    
    if not normalized:
        return ""
    
    if headers == "keys" and isinstance(table, dict):
        headers = list(table.keys())
    elif isinstance(headers, (list, tuple)):
        headers = list(headers)
    else:
        headers = []
    
    if headers:
        normalized = [headers] + normalized
    
    if showindex:
        if headers:
            headers.insert(0, "")
        for i, row in enumerate(normalized[1:], 1):
            row.insert(0, str(i - 1))
    
    tablefmt = _FORMAT_ALIASES.get(tablefmt, tablefmt)
    format_spec = _TABLE_FORMATS.get(tablefmt, _TABLE_FORMATS["plain"])
    
    if isinstance(align, str):
        align = [align] * len(normalized[0]) if normalized else []
    elif align is None:
        align = []
        for col in zip(*normalized):
            if any(re.search(r"^-?\d+\.\d+$", cell) for cell in col):
                align.append(numalign)
            else:
                align.append(stralign)
    
    widths = _calculate_column_widths(normalized)
    
    formatted_rows = []
    for i, row in enumerate(normalized):
        is_header = i == 0 and headers
        is_separator = False
        
        edge, sep = format_spec["edge"], format_spec["sep"]
        if is_header and "header" in format_spec:
            edge, sep = format_spec["header"]["edge"], format_spec["header"]["sep"]
        elif i == 1 and headers and "top" in format_spec:
            edge, sep = format_spec["top"]["edge"], format_spec["top"]["sep"]
            is_separator = True
        elif i > 0 and "mid" in format_spec:
            edge, sep = format_spec["mid"]["edge"], format_spec["mid"]["sep"]
            is_separator = True
        elif i == len(normalized) - 1 and "bottom" in format_spec:
            edge, sep = format_spec["bottom"]["edge"], format_spec["bottom"]["sep"]
            is_separator = True
        
        if is_separator:
            row = [format_spec["sep_char"] * width for width in widths]
        
        formatted_row = _format_row(
            row,
            widths,
            align,
            format_spec["padding"],
            edge[0],
            sep,
            edge[1],
        )
        formatted_rows.append(formatted_row)
    
    return "\n".join(formatted_rows)

def simple_separated_format(separator: str) -> dict:
    """Create a simple table format with the given separator."""
    return {
        "edge": ("", ""),
        "sep": separator,
        "padding": 0,
    }
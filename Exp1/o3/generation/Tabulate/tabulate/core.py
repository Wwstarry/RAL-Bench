"""
Core implementation of the *tabulate* public API.
Only a pragmatic subset of the original library is provided.
"""

from __future__ import annotations

import decimal
import itertools
import numbers
import sys
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

from .formats import TABLE_FORMATS

__all__ = [
    "tabulate",
    "simple_separated_format",
]

# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _is_numeric(value: Any) -> bool:
    """A very small helper to determine if *value* represents a number."""
    return isinstance(value, (int, float, complex, decimal.Decimal)) and not isinstance(
        value, bool
    )


def _to_str(value: Any, floatfmt: str, missingval: str) -> str:
    """Convert *value* to string applying formats."""
    if value is None:
        return missingval
    if isinstance(value, float):
        try:
            return format(value, floatfmt)
        except Exception:
            # Fallback to default str()
            return str(value)
    return str(value)


def _split_lines(text: str) -> List[str]:
    """Return *text* split onto lines."""
    return text.split("\n")


def _infer_headers_from_dicts(dict_rows: Sequence[Mapping[str, Any]]) -> List[str]:
    """Return an ordered set of keys – preserving order of appearance."""
    seen = []
    for row in dict_rows:
        for k in row.keys():
            if k not in seen:
                seen.append(k)
    return seen


# --------------------------------------------------------------------------- #
# Public user-facing utilities
# --------------------------------------------------------------------------- #


def simple_separated_format(sep: str = " "):
    """
    Return a *formatting function* compatible with the official
    ``tabulate.simple_separated_format`` helper.

    Example
    -------
    >>> tsv = simple_separated_format("\\t")
    >>> print(tsv([[1, 2], [3, 4]]))
    1   2
    3   4
    """

    def _formatter(tabular_data, headers=(), **kwargs):
        return tabulate(tabular_data, headers=headers, tablefmt="plain", **kwargs).replace(
            " ", sep
        )

    return _formatter


# --------------------------------------------------------------------------- #
# Normalisation of the user supplied *tabular data*
# --------------------------------------------------------------------------- #


def _as_rows(
    tabular_data: Any,
    headers: Any,
    missingval: str,
) -> Tuple[List[List[Any]], List[str]]:
    """
    Return ``(rows, headers)`` where *rows* is ``List[List[Any]]`` and
    *headers* is a list of strings suitable for rendering.
    """
    # 1. If *tabular_data* is a mapping treat it as single-row table
    if isinstance(tabular_data, Mapping):
        keys = list(tabular_data.keys())
        _headers: List[str]
        if headers == "keys" or headers in ((), None, False):
            _headers = ["key", "value"]
        elif isinstance(headers, Sequence) and not isinstance(headers, str):
            _headers = list(headers)
        else:
            _headers = []
        return [[k, tabular_data[k]] for k in keys], _headers

    # 2. list-of-dicts handling
    if isinstance(tabular_data, Sequence) and tabular_data and isinstance(
        tabular_data[0], Mapping
    ):
        dict_rows = list(tabular_data)  # type: ignore[arg-type]
        if headers == "keys" or headers in ((), None, False):
            hdrs = _infer_headers_from_dicts(dict_rows)
        elif isinstance(headers, Sequence) and not isinstance(headers, str):
            hdrs = list(headers)
        else:
            hdrs = _infer_headers_from_dicts(dict_rows)

        rows: List[List[Any]] = []
        for d in dict_rows:
            row = [d.get(key, missingval) for key in hdrs]
            rows.append(row)
        return rows, hdrs

    # 3. Generic sequence of sequences
    if isinstance(tabular_data, Sequence):
        rows = [list(r) if isinstance(r, Sequence) else [r] for r in tabular_data]  # type: ignore
    else:
        # Fallback: treat the object as a scalar -> single cell table
        rows = [[tabular_data]]

    # headers second
    if headers == "keys":
        headers_list: List[str] = []
    elif isinstance(headers, Sequence) and not isinstance(headers, str):
        headers_list = list(headers)
    else:
        headers_list = []

    return rows, headers_list


# --------------------------------------------------------------------------- #
# The actual renderer
# --------------------------------------------------------------------------- #


def tabulate(
    tabular_data: Any,
    headers: Any = (),
    tablefmt: str = "simple",
    showindex: bool | Sequence[Any] = False,
    stralign: str | None = "left",
    numalign: str | None = "decimal",
    floatfmt: str = "g",
    missingval: str = "",
) -> str:
    """
    Format *tabular_data* into a table.

    Only a subset of arguments of the original *tabulate* function
    is implemented, but the most frequently used ones are present.
    """

    fmt = TABLE_FORMATS.get(tablefmt)
    if fmt is None:
        raise ValueError(f"Unknown table format {tablefmt!r}")

    rows, hdrs = _as_rows(tabular_data, headers, missingval)

    # Insert header into rows if requested by original API
    if hdrs:
        # If headers is list of tuples may contain formatting for header row
        pass

    # Prepend index column if requested
    if showindex not in (False, None, "default"):
        if showindex is True:
            indices = list(range(len(rows)))
        elif isinstance(showindex, Sequence):
            indices = list(showindex)
        else:
            # showindex is something truthy: fallback to range
            indices = list(range(len(rows)))
        hdrs = [""] + hdrs
        for idx, row in enumerate(rows):
            row.insert(0, indices[idx])

    # Compute cell strings
    str_rows: List[List[str]] = []

    processed_rows: List[List[Any]] = []

    # First, create header row (string) list
    if hdrs:
        processed_rows.append(hdrs)

    processed_rows.extend(rows)

    for row in processed_rows:
        str_row = []
        for cell in row:
            s = _to_str(cell, floatfmt=floatfmt, missingval=missingval)
            str_row.append(s)
        str_rows.append(str_row)

    # Column widths
    num_cols = max(len(r) for r in str_rows)
    # Normalize rows length
    for r in str_rows:
        if len(r) < num_cols:
            r.extend([""] * (num_cols - len(r)))

    col_widths: List[int] = [0] * num_cols
    # for every column compute max width considering multiline cells
    for col in range(num_cols):
        maxw = 0
        for row in str_rows:
            cell_lines = _split_lines(row[col])
            for l in cell_lines:
                maxw = max(maxw, len(l))
        col_widths[col] = maxw

    # Determine alignment for each column: numeric vs string (scan data rows, not headers)
    col_is_numeric = [False] * num_cols
    data_only = str_rows[1:] if hdrs else str_rows
    for col in range(num_cols):
        for r, orig_row in enumerate(rows):
            if col < len(orig_row) and _is_numeric(orig_row[col]):
                col_is_numeric[col] = True
                break

    col_align: List[str] = []
    for isnum in col_is_numeric:
        if isnum:
            col_align.append(numalign or "right")
        else:
            col_align.append(stralign or "left")

    # Build all rows string lines (handle multiline)
    rendered_lines: List[str] = []

    def _pad(text: str, width: int, align: str) -> str:
        # align can be 'left', 'right', 'center', 'decimal'
        if align == "left":
            return text.ljust(width)
        elif align == "right":
            return text.rjust(width)
        elif align == "center":
            return text.center(width)
        elif align == "decimal":
            # Align at decimal point
            if "." in text:
                integer, frac = text.split(".", 1)
            else:
                integer, frac = text, ""
            offset = width - len(text)
            return " " * offset + text
        else:
            return text.ljust(width)

    # Precompute borders
    lineabove_fn = fmt["lineabove"]
    headerline_fn = fmt["headerline"]
    linebetween_fn = fmt["linebetween"]
    linebelow_fn = fmt["linebelow"]

    row_open = fmt["row_open"]
    row_close = fmt["row_close"]
    row_sep = fmt["row_sep"]

    if hdrs and lineabove_fn is not None:
        rendered_lines.append(lineabove_fn(col_widths))
    elif not hdrs and lineabove_fn is not None:
        rendered_lines.append(lineabove_fn(col_widths))

    for ridx, (orig_row, row) in enumerate(zip(processed_rows, str_rows)):
        # produce cell lines
        cell_lines_per_col: List[List[str]] = []
        max_height = 1
        for cidx, cell in enumerate(row):
            lines = _split_lines(cell)
            max_height = max(max_height, len(lines))
            cell_lines_per_col.append(lines)

        for i in range(max_height):
            parts = []
            for cidx, lines in enumerate(cell_lines_per_col):
                content = lines[i] if i < len(lines) else ""
                parts.append(_pad(content, col_widths[cidx], col_align[cidx]))
            rendered_line = row_open + row_sep.join(parts) + row_close
            rendered_lines.append(rendered_line)

        # header line
        if hdrs and ridx == 0 and headerline_fn is not None:
            rendered_lines.append(headerline_fn(col_widths))
        elif (
            ridx >= (1 if hdrs else 0)
            and ridx != len(processed_rows) - 1
            and linebetween_fn is not None
        ):
            rendered_lines.append(linebetween_fn(col_widths))
    if linebelow_fn is not None:
        rendered_lines.append(linebelow_fn(col_widths))

    # For plain/tsv/csv: they have empty row_open etc causing trailing spaces; strip them
    if tablefmt in ("plain", "tsv", "csv"):
        rendered_lines = [ln.rstrip() for ln in rendered_lines if ln.strip() != ""]

    return "\n".join(rendered_lines)
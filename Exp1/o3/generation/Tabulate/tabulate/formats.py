"""
Definitions of the supported *table formats*.

Each format description is a (dict-like) mapping with the
following keys:

* 'lineabove'   – line printed before the first data/header row
* 'linebelow'   – line printed after the final row
* 'linebetween' – line printed between data rows
* 'headerline'  – line printed right after the header row
* 'row_open'    – string printed at the very beginning of each row
* 'row_close'   – string printed at the very end   of each row
* 'row_sep'     – separator between cells inside a row

The placeholders ``{fills}`` and ``{widths}`` are replaced later
by :pyfunc:`tabulate.core._build_border`.
"""

from __future__ import annotations

from typing import Dict, List

__all__ = ["TABLE_FORMATS"]

# sentinel used inside format templates when a particular border is absent
_NO = None  # type: ignore

# Helper util to build '+----+------+-----+' style borders
def _build_border(
    left: str | None,
    fills: List[str],
    junction: str | None,
    right: str | None,
) -> str | None:
    if left is None and right is None and junction is None:
        # Entire line is disabled for this table format.
        return None
    pieces: List[str] = []
    if left is not None:
        pieces.append(left)
    for idx, fill in enumerate(fills):
        pieces.append(fill)
        if idx != len(fills) - 1 and junction is not None:
            pieces.append(junction)
    if right is not None:
        pieces.append(right)
    return "".join(pieces)


def _line_factory(
    left: str | None,
    horizontal: str | None,
    junction: str | None,
    right: str | None,
):
    """
    Returns a callable that, given a list of column widths,
    constructs a horizontal border. ``horizontal`` describes the
    fill character, ``junction`` the separator between columns.
    """
    if horizontal is None:
        # fully disabled – no line at all
        return None

    def _builder(widths):
        fills = [horizontal * (w + 2) for w in widths]  # 2 == padding each side
        return _build_border(left, fills, junction, right)

    return _builder


def _row_prefix_suffix(prefix: str | None, suffix: str | None, sep: str):
    """Return the three row oriented components expected by the renderer."""
    return {
        "row_open": prefix or "",
        "row_close": suffix or "",
        "row_sep": sep,
    }


# --------------------------------------------------------------------------- #
# Concrete table formats.
# --------------------------------------------------------------------------- #
TABLE_FORMATS: Dict[str, dict] = {}


def _register(name: str, *, borders: dict, row: dict):
    fmt = {**borders, **row}
    TABLE_FORMATS[name] = fmt
    return fmt


# Plain – space separated, no borders at all
_register(
    "plain",
    borders={
        "lineabove": None,
        "headerline": None,
        "linebetween": None,
        "linebelow": None,
    },
    row=_row_prefix_suffix("", "", " "),
)

# Simple – header underline using '-' and ' ' as cell sep
_register(
    "simple",
    borders={
        "lineabove": None,
        "headerline": _line_factory(None, "-", " ", None),
        "linebetween": None,
        "linebelow": None,
    },
    row=_row_prefix_suffix("", "", " "),
)

# Grid – classic ascii-grid style (`+---+`), border above/below/inside
_grid_borders = {
    "lineabove": _line_factory("+", "-", "+", "+"),
    "headerline": _line_factory("+", "=", "+", "+"),
    "linebetween": _line_factory("+", "-", "+", "+"),
    "linebelow": _line_factory("+", "-", "+", "+"),
}
_register(
    "grid",
    borders=_grid_borders,
    row=_row_prefix_suffix("| ", " |", " | "),
)

# Pipe – GitHub / Markdown pipe table
_pipe_borders = {
    "lineabove": None,
    "headerline": _line_factory("|", "-", "|", "|"),
    "linebetween": None,
    "linebelow": None,
}
_register(
    "pipe",
    borders=_pipe_borders,
    row=_row_prefix_suffix("| ", " |", " | "),
)

# TSV (tab separated)
_register(
    "tsv",
    borders={
        "lineabove": None,
        "headerline": None,
        "linebetween": None,
        "linebelow": None,
    },
    row=_row_prefix_suffix("", "", "\t"),
)

# CSV (comma separated)
_register(
    "csv",
    borders={
        "lineabove": None,
        "headerline": None,
        "linebetween": None,
        "linebelow": None,
    },
    row=_row_prefix_suffix("", "", ","),
)
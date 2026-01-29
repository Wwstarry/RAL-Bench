from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class TableFormat:
    # Characters for drawing tables. If None, that part is not used.
    lineabove: Optional[str] = None
    linebelow: Optional[str] = None
    linebetweenrows: Optional[str] = None
    linebetweencolumns: Optional[str] = None

    # Header separation line (between header and data). If None, reuse linebetweenrows.
    lineheader: Optional[str] = None

    # Column padding. Typical is 1 for grid, 0 for plain.
    pad: int = 1

    # How to separate columns if not using a box. If None and no vertical line, use spaces.
    colsep: Optional[str] = None

    # Minimal/compat flags
    headerrow: bool = True  # whether header participates
    # output "as is" without line decorations (used mainly by "plain")
    plaintext: bool = False

    # For TSV/CSV like
    rowsep: str = "\n"

    # For "html" like
    is_html: bool = False
    table_open: str = "<table>"
    table_close: str = "</table>"
    thead_open: str = "<thead>"
    thead_close: str = "</thead>"
    tbody_open: str = "<tbody>"
    tbody_close: str = "</tbody>"
    tr_open: str = "<tr>"
    tr_close: str = "</tr>"
    th_open: str = "<th>"
    th_close: str = "</th>"
    td_open: str = "<td>"
    td_close: str = "</td>"


def simple_separated_format(separator: str) -> TableFormat:
    # For csv/tsv-like: no extra padding; join with separator; no borders.
    return TableFormat(
        lineabove=None,
        linebelow=None,
        linebetweenrows=None,
        linebetweencolumns=None,
        lineheader=None,
        pad=0,
        colsep=separator,
        plaintext=True,
    )


# A tiny box-drawing "grid" (ASCII) close to reference expectations.
# Use '+' corners, '-' horizontals, '|' verticals.
grid = TableFormat(
    lineabove="+{sep}+",
    linebelow="+{sep}+",
    linebetweenrows="+{sep}+",
    lineheader="+{sep}+",
    linebetweencolumns="|",
    pad=1,
    colsep=" | ",
    plaintext=False,
)

plain = TableFormat(
    lineabove=None,
    linebelow=None,
    linebetweenrows=None,
    lineheader=None,
    linebetweencolumns=None,
    pad=0,
    colsep="  ",
    plaintext=True,
)

# GitHub-flavored markdown pipe style.
pipe = TableFormat(
    lineabove=None,
    linebelow=None,
    linebetweenrows=None,
    lineheader="|{sep}|",
    linebetweencolumns="|",
    pad=1,
    colsep=" | ",
    plaintext=False,
)

# Minimal HTML.
html = TableFormat(
    plaintext=False,
    is_html=True,
    pad=0,
)

# TSV/CSV shortcuts
tsv = simple_separated_format("\t")
csv = simple_separated_format(",")

tabulate_formats: Dict[str, TableFormat] = {
    "plain": plain,
    "simple": plain,  # common alias in reference
    "grid": grid,
    "pipe": pipe,
    "github": pipe,  # common alias
    "tsv": tsv,
    "csv": csv,
    "html": html,
}
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class Line:
    begin: str = ""
    hline: str = ""
    sep: str = ""
    end: str = ""


@dataclass(frozen=True)
class Row:
    begin: str = ""
    sep: str = " "
    end: str = ""


@dataclass(frozen=True)
class TableFormat:
    lineabove: Optional[Line] = None
    linebelow: Optional[Line] = None
    linebetweenrows: Optional[Line] = None
    linebelowheader: Optional[Line] = None

    headerrow: Optional[Row] = None
    datarow: Optional[Row] = None

    padding: int = 0

    # Upstream has `with_header_hide`; keep attribute for compatibility.
    with_header_hide: Optional[list] = None


def simple_separated_format(sep: str = "\t") -> TableFormat:
    """Return a simple separator-only format (no borders, no padding)."""
    return TableFormat(
        lineabove=None,
        linebelow=None,
        linebetweenrows=None,
        linebelowheader=None,
        headerrow=Row(begin="", sep=sep, end=""),
        datarow=Row(begin="", sep=sep, end=""),
        padding=0,
    )


# ----- Built-in table formats -----

# Plain: minimal space-separated columns, no header rule by default.
plain = TableFormat(
    lineabove=None,
    linebelow=None,
    linebetweenrows=None,
    linebelowheader=None,
    headerrow=Row(begin="", sep="  ", end=""),
    datarow=Row(begin="", sep="  ", end=""),
    padding=0,
)

# Simple: space-separated columns with a dashed header separator.
simple = TableFormat(
    lineabove=None,
    linebelow=None,
    linebetweenrows=None,
    linebelowheader=Line(begin="", hline="-", sep="  ", end=""),
    headerrow=Row(begin="", sep="  ", end=""),
    datarow=Row(begin="", sep="  ", end=""),
    padding=0,
)

# Grid: ASCII box drawing using +-| with padding=1.
grid = TableFormat(
    lineabove=Line(begin="+", hline="-", sep="+", end="+"),
    linebelow=Line(begin="+", hline="-", sep="+", end="+"),
    linebetweenrows=Line(begin="+", hline="-", sep="+", end="+"),
    linebelowheader=Line(begin="+", hline="-", sep="+", end="+"),
    headerrow=Row(begin="|", sep="|", end="|"),
    datarow=Row(begin="|", sep="|", end="|"),
    padding=1,
)

# Pipe: GitHub-flavored markdown-ish. We'll render header separator ourselves
# as a linebelowheader "hline" made of '-' and optional ':' based on alignment.
pipe = TableFormat(
    lineabove=None,
    linebelow=None,
    linebetweenrows=None,
    linebelowheader=Line(begin="|", hline="-", sep="|", end="|"),
    headerrow=Row(begin="|", sep="|", end="|"),
    datarow=Row(begin="|", sep="|", end="|"),
    padding=1,
)

tsv = simple_separated_format("\t")
csv = simple_separated_format(",")

# HTML is special-cased in core rendering, but still provide a format entry.
html = TableFormat(
    headerrow=Row(begin="", sep="", end=""),
    datarow=Row(begin="", sep="", end=""),
    padding=0,
)

table_formats: Dict[str, TableFormat] = {
    "plain": plain,
    "simple": simple,
    "grid": grid,
    "pipe": pipe,
    "tsv": tsv,
    "csv": csv,
    "html": html,
}
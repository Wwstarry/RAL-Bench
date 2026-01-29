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
class DataRow:
    begin: str = ""
    sep: str = " "
    end: str = ""


@dataclass(frozen=True)
class TableFormat:
    lineabove: Optional[Line] = None
    linebelowheader: Optional[Line] = None
    linebetweenrows: Optional[Line] = None
    linebelow: Optional[Line] = None
    headerrow: DataRow = DataRow()
    datarow: DataRow = DataRow()
    padding: int = 0
    with_header_hide: Optional[list] = None


def simple_separated_format(sep: str = "\t") -> TableFormat:
    # Similar to tabulate's simple_separated_format: no borders, separator only.
    return TableFormat(
        lineabove=None,
        linebelowheader=None,
        linebetweenrows=None,
        linebelow=None,
        headerrow=DataRow(begin="", sep=sep, end=""),
        datarow=DataRow(begin="", sep=sep, end=""),
        padding=0,
    )


# Preset formats (core subset)
tabulate_formats: Dict[str, TableFormat] = {}

# plain: whitespace separated, no borders
tabulate_formats["plain"] = TableFormat(
    lineabove=None,
    linebelowheader=None,
    linebetweenrows=None,
    linebelow=None,
    headerrow=DataRow(begin="", sep="  ", end=""),
    datarow=DataRow(begin="", sep="  ", end=""),
    padding=0,
)

# simple: like plain but with a header underline (---)
tabulate_formats["simple"] = TableFormat(
    lineabove=None,
    linebelowheader=Line(begin="", hline="-", sep="  ", end=""),
    linebetweenrows=None,
    linebelow=None,
    headerrow=DataRow(begin="", sep="  ", end=""),
    datarow=DataRow(begin="", sep="  ", end=""),
    padding=0,
)

# grid: +----+ with | cells |
tabulate_formats["grid"] = TableFormat(
    lineabove=Line(begin="+", hline="-", sep="+", end="+"),
    linebelowheader=Line(begin="+", hline="=", sep="+", end="+"),
    linebetweenrows=Line(begin="+", hline="-", sep="+", end="+"),
    linebelow=Line(begin="+", hline="-", sep="+", end="+"),
    headerrow=DataRow(begin="|", sep="|", end="|"),
    datarow=DataRow(begin="|", sep="|", end="|"),
    padding=1,
)

# pipe: GitHub markdown
tabulate_formats["pipe"] = TableFormat(
    lineabove=None,
    linebelowheader=Line(begin="|", hline="-", sep="|", end="|"),
    linebetweenrows=None,
    linebelow=None,
    headerrow=DataRow(begin="|", sep="|", end="|"),
    datarow=DataRow(begin="|", sep="|", end="|"),
    padding=1,
)

# github is an alias of pipe in tabulate
tabulate_formats["github"] = tabulate_formats["pipe"]

# tsv/csv
tabulate_formats["tsv"] = simple_separated_format("\t")
tabulate_formats["csv"] = simple_separated_format(",")

# html: simplified html table
# (Reference tabulate supports attributes; this is a core-compatible subset.)
tabulate_formats["html"] = TableFormat(
    lineabove=None,
    linebelowheader=None,
    linebetweenrows=None,
    linebelow=None,
    headerrow=DataRow(begin="<tr>", sep="", end="</tr>"),
    datarow=DataRow(begin="<tr>", sep="", end="</tr>"),
    padding=0,
)

# jira style: || header || and | rows |
tabulate_formats["jira"] = TableFormat(
    lineabove=None,
    linebelowheader=None,
    linebetweenrows=None,
    linebelow=None,
    headerrow=DataRow(begin="||", sep="||", end="||"),
    datarow=DataRow(begin="|", sep="|", end="|"),
    padding=1,
)

# orgtbl: Emacs org-mode tables
tabulate_formats["orgtbl"] = TableFormat(
    lineabove=None,
    linebelowheader=Line(begin="|", hline="-", sep="+", end="|"),
    linebetweenrows=None,
    linebelow=None,
    headerrow=DataRow(begin="|", sep="|", end="|"),
    datarow=DataRow(begin="|", sep="|", end="|"),
    padding=1,
)
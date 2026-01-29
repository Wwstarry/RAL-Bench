import re
import sys
import html as _html
from decimal import Decimal
from typing import Any, Iterable, List, Mapping, Optional, Sequence, Tuple, Union

from .formats import AVAILABLE_FORMATS, SeparatedFormat, simple_separated_format as _simple_sep_fmt

# Public factory for separated formats
def simple_separated_format(sep: str) -> SeparatedFormat:
    return _simple_sep_fmt(sep)


# Numeric detection regex for numeric-looking strings
_NUMERIC_RE = re.compile(
    r"""
^\s*
(?P<sign>[+-]?)(
  (
    (\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?   # float/exponent
  )
  |
  (\d+)                                   # or plain int
)
\s*$
""",
    re.X,
)

def _is_number(value: Any) -> bool:
    # treat ints, floats, Decimal as numbers, but exclude booleans
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float, Decimal)):
        return True
    # strings that look like numbers
    if isinstance(value, str):
        return bool(_NUMERIC_RE.match(value))
    return False


def _to_str(value: Any, floatfmt: str, missingval: str) -> str:
    if value is None:
        return missingval
    # leave strings unchanged
    if isinstance(value, str):
        return value
    # handle Decimal/float
    if isinstance(value, (float, Decimal)):
        try:
            return format(value, floatfmt)
        except Exception:
            # fallback to str if format spec fails
            return str(value)
    return str(value)


def _split_lines(s: str) -> List[str]:
    # preserve empty lines as empty strings (splitlines() would skip trailing empties without keepends)
    return s.split("\n")


def _stringify_table(
    rows: List[List[Any]],
    headers: Optional[List[Any]],
    floatfmt: str,
    missingval: str,
) -> Tuple[Optional[List[List[str]]], List[List[List[str]]], List[List[bool]]]:
    """
    Convert all cells to strings; keep multiline by splitting at newline.
    Returns:
        headers_lines: list of list of lines per header cell or None
        rows_lines: list of rows; each row is list of list-of-lines
        rows_isnum: same structure as rows_lines, but each cell a boolean is-number
    """
    headers_lines: Optional[List[List[str]]] = None
    if headers is not None:
        headers_lines = []
        for h in headers:
            hs = _to_str(h, floatfmt, missingval)
            headers_lines.append(_split_lines(hs))

    rows_lines: List[List[List[str]]] = []
    rows_isnum: List[List[bool]] = []
    for row in rows:
        out_row: List[List[str]] = []
        out_isnum: List[bool] = []
        for cell in row:
            isnum = _is_number(cell)
            s = _to_str(cell, floatfmt, missingval)
            out_row.append(_split_lines(s))
            out_isnum.append(isnum)
        rows_lines.append(out_row)
        rows_isnum.append(out_isnum)
    return headers_lines, rows_lines, rows_isnum


def _normalize_tabular_data(
    tabular_data: Any,
    headers: Union[Sequence[Any], str, None],
    missingval: str,
) -> Tuple[Optional[List[Any]], List[List[Any]]]:
    """
    Normalize input into headers list (or None) and list of rows (lists).
    Handles:
    - list of lists/tuples
    - dict of columns
    - list of dicts (records)
    """
    # Mapping of columns
    if isinstance(tabular_data, Mapping):
        # dict of columns
        keys = list(tabular_data.keys())
        if headers == "keys" or headers is None:
            hdrs = keys
        elif headers == "firstrow":
            # Not meaningful for dict of columns; treat as keys
            hdrs = keys
        else:
            hdrs = list(headers) if headers is not None else keys

        # sequence lengths; handle shorter columns by missingval None (to be stringified later)
        cols = [list(tabular_data.get(k, [])) for k in hdrs]
        n_rows = max((len(c) for c in cols), default=0)
        out_rows: List[List[Any]] = []
        for i in range(n_rows):
            r = []
            for c in cols:
                r.append(c[i] if i < len(c) else None)
            out_rows.append(r)
        return list(hdrs), out_rows

    # List of dicts?
    if isinstance(tabular_data, (list, tuple)) and tabular_data and isinstance(tabular_data[0], Mapping):
        # Collect headers from union of keys in the order first seen
        key_order: List[Any] = []
        seen = set()
        for d in tabular_data:
            for k in d.keys():
                if k not in seen:
                    seen.add(k)
                    key_order.append(k)

        if headers == "keys" or headers is None:
            hdrs = key_order
        elif headers == "firstrow":
            # Not meaningful for list of dicts
            hdrs = key_order
        else:
            hdrs = list(headers) if headers is not None else key_order

        out_rows: List[List[Any]] = []
        for d in tabular_data:
            out_rows.append([d.get(k, None) for k in hdrs])
        return list(hdrs), out_rows

    # Otherwise, treat as sequence of rows
    # Convert to list of lists
    rows: List[List[Any]] = [list(r) if isinstance(r, (list, tuple)) else [r] for r in (tabular_data or [])]
    hdrs_out: Optional[List[Any]] = None
    if headers == "firstrow" and rows:
        hdrs_out = list(rows[0])
        rows = rows[1:]
    elif headers in (None, ()):
        hdrs_out = None
    elif headers == "keys":
        # No keys here, leave None
        hdrs_out = None
    else:
        hdrs_out = list(headers) if headers is not None else None
    # If headers provided but rows columns mismatch, pad rows
    ncols = max(len(r) for r in rows) if rows else (len(hdrs_out) if hdrs_out is not None else 0)
    if hdrs_out is not None and len(hdrs_out) < ncols:
        # pad headers
        hdrs_out = hdrs_out + [None] * (ncols - len(hdrs_out))
    for r in rows:
        if len(r) < ncols:
            r.extend([None] * (ncols - len(r)))
    return hdrs_out, rows


def _compute_col_widths(
    headers_lines: Optional[List[List[str]]],
    rows_lines: List[List[List[str]]],
) -> List[int]:
    # Determine number of columns
    ncols = 0
    if headers_lines is not None:
        ncols = max(ncols, len(headers_lines))
    for row in rows_lines:
        ncols = max(ncols, len(row))
    widths = [0] * ncols
    # headers
    if headers_lines is not None:
        for i, lines in enumerate(headers_lines):
            for ln in lines:
                widths[i] = max(widths[i], len(ln))
    # rows
    for row in rows_lines:
        for i, cell_lines in enumerate(row):
            for ln in cell_lines:
                widths[i] = max(widths[i], len(ln))
    return widths


def _pad_text(text: str, width: int, align: str) -> str:
    if align not in ("left", "right", "center", "decimal"):
        align = "left"
    # Treat decimal like right for this simplified implementation
    if align == "decimal":
        align = "right"
    length = len(text)
    if length >= width:
        return text
    space = width - length
    if align == "left":
        return text + " " * space
    elif align == "right":
        return " " * space + text
    else:  # center
        left = space // 2
        right = space - left
        return " " * left + text + " " * right


def _render_plain(headers_lines, rows_lines, rows_isnum, widths, numalign, stralign) -> str:
    lines: List[str] = []
    # helper to render one logical row, possibly multiline
    def render_row(row_lines: List[List[str]], row_isnum: List[bool]) -> List[str]:
        if not row_lines:
            return [""]
        maxh = max(len(c) for c in row_lines)
        out: List[str] = []
        for i in range(maxh):
            parts: List[str] = []
            for col, cell_lines in enumerate(row_lines):
                line = cell_lines[i] if i < len(cell_lines) else ""
                align = numalign if row_isnum[col] else stralign
                parts.append(_pad_text(line, widths[col], align))
            out.append(" ".join(parts).rstrip())
        return out

    if headers_lines is not None and headers_lines:
        # Align headers like data based on content numeric detection: treat headers as strings.
        hdr_isnum = [False] * len(headers_lines)
        lines.extend(render_row([headers_lines[i] for i in range(len(headers_lines))], hdr_isnum))
    if headers_lines is not None and headers_lines:
        # plain has no header separator
        pass
    for r, isnum in zip(rows_lines, rows_isnum):
        lines.extend(render_row(r, isnum))
    return "\n".join(lines)


def _render_simple(headers_lines, rows_lines, rows_isnum, widths, numalign, stralign) -> str:
    lines: List[str] = []

    def render_row(row_lines: List[List[str]], row_isnum: List[bool]) -> List[str]:
        if not row_lines:
            return [""]
        maxh = max(len(c) for c in row_lines)
        out: List[str] = []
        for i in range(maxh):
            parts: List[str] = []
            for col, cell_lines in enumerate(row_lines):
                line = cell_lines[i] if i < len(cell_lines) else ""
                align = numalign if row_isnum[col] else stralign
                parts.append(_pad_text(line, widths[col], align))
            out.append(" ".join(parts).rstrip())
        return out

    if headers_lines is not None and headers_lines:
        hdr_isnum = [False] * len(headers_lines)
        hdr_rows = render_row([headers_lines[i] for i in range(len(headers_lines))], hdr_isnum)
        lines.extend(hdr_rows)
        # header separator: dashes equal to width
        sep = " ".join("-" * w if w > 0 else "" for w in widths).rstrip()
        lines.append(sep)
    for r, isnum in zip(rows_lines, rows_isnum):
        lines.extend(render_row(r, isnum))
    return "\n".join(lines)


def _hline_grid(widths: List[int]) -> str:
    # +-----+----+ style
    segs = ["+" + "-" * (w + 2) for w in widths]
    return "".join(segs) + "+"


def _render_grid(headers_lines, rows_lines, rows_isnum, widths, numalign, stralign) -> str:
    lines: List[str] = []
    # top border
    lines.append(_hline_grid(widths))

    def render_row(row_lines: List[List[str]], row_isnum: List[bool]) -> List[str]:
        if not row_lines:
            return ["|" + " " * sum(w + 2 for w in widths) + "|"]
        maxh = max(len(c) for c in row_lines)
        out: List[str] = []
        for i in range(maxh):
            parts: List[str] = []
            for col, cell_lines in enumerate(row_lines):
                line = cell_lines[i] if i < len(cell_lines) else ""
                align = numalign if row_isnum[col] else stralign
                padded = _pad_text(line, widths[col], align)
                parts.append(" " + padded + " ")
            out.append("|" + "|".join(parts) + "|")
        return out

    if headers_lines is not None and headers_lines:
        hdr_isnum = [False] * len(headers_lines)
        lines.extend(render_row([headers_lines[i] for i in range(len(headers_lines))], hdr_isnum))
        lines.append(_hline_grid(widths))
    for r, isnum in zip(rows_lines, rows_isnum):
        lines.extend(render_row(r, isnum))
        lines.append(_hline_grid(widths))
    return "\n".join(lines)


def _render_pipe(headers_lines, rows_lines, rows_isnum, widths, numalign, stralign, colalign: Optional[Sequence[Optional[str]]] = None) -> str:
    lines: List[str] = []

    def render_row(row_lines: List[List[str]], row_isnum: List[bool]) -> List[str]:
        if not row_lines:
            return ["||"]
        maxh = max(len(c) for c in row_lines)
        out: List[str] = []
        for i in range(maxh):
            parts: List[str] = []
            for col, cell_lines in enumerate(row_lines):
                line = cell_lines[i] if i < len(cell_lines) else ""
                # decide per-cell alignment; for markdown, we still align strings inside padding
                align = numalign if row_isnum[col] else stralign
                padded = _pad_text(line, widths[col], align)
                parts.append(" " + padded + " ")
            out.append("|" + "|".join(parts) + "|")
        return out

    if headers_lines is not None and headers_lines:
        hdr_isnum = [False] * len(headers_lines)
        lines.extend(render_row([headers_lines[i] for i in range(len(headers_lines))], hdr_isnum))
        # header alignment row of dashes with colons
        header_aligns: List[str] = []
        ncols = len(widths)
        # choose column alignment: based on provided colalign, else if any numeric in column -> numalign else stralign
        # Determine per-column numeric presence
        col_has_num = [False] * ncols
        for row_is in rows_isnum:
            for i, b in enumerate(row_is):
                if b:
                    col_has_num[i] = True
        for i, w in enumerate(widths):
            # prefer colalign if given
            align = None
            if colalign and i < len(colalign) and colalign[i]:
                align = colalign[i]
            else:
                align = numalign if col_has_num[i] else stralign
            align = {"l": "left", "r": "right", "c": "center"}.get(str(align).lower(), str(align))
            if align == "right" or align == "decimal":
                # ---:
                if w <= 1:
                    s = "-" * (w) + ":"
                else:
                    s = "-" * (w - 1) + ":"
            elif align == "center":
                # :---:
                if w == 0:
                    s = "::"
                elif w == 1:
                    s = ":-:"
                else:
                    s = ":" + "-" * (w - 2) + ":"
            else:  # left/default
                # :---
                if w <= 1:
                    s = ":" + "-" * (w)
                else:
                    s = ":" + "-" * (w - 1)
            header_aligns.append(" " + s + " ")
        lines.append("|" + "|".join(header_aligns) + "|")
    for r, isnum in zip(rows_lines, rows_isnum):
        lines.extend(render_row(r, isnum))
    return "\n".join(lines)


def _render_separated(
    headers_lines,
    rows_lines,
    rows_isnum,
    sep: str,
) -> str:
    # separated values: no padding/align; multiline cells are joined with \n within cell
    out_lines: List[str] = []
    if headers_lines is not None and headers_lines:
        hdr = sep.join("".join(h) for h in headers_lines)
        out_lines.append(hdr)
    for row in rows_lines:
        out_lines.append(sep.join("".join(cell) for cell in row))
    return "\n".join(out_lines)


def _render_html(
    headers_lines,
    rows_lines,
    rows_isnum,
) -> str:
    # Minimal HTML table
    # escape cell contents
    parts: List[str] = []
    parts.append("<table>")
    if headers_lines is not None and headers_lines:
        parts.append("  <thead>")
        parts.append("    <tr>")
        for h in headers_lines:
            # if multiline header, join with <br>
            content = _html.escape("<br>".join(h))
            # but escape replaced < and > again double; Instead join escaped lines with <br/>
            content = "<br>".join(_html.escape(line) for line in h)
            parts.append(f"      <th>{content}</th>")
        parts.append("    </tr>")
        parts.append("  </thead>")
    parts.append("  <tbody>")
    for row in rows_lines:
        parts.append("    <tr>")
        for cell in row:
            content = "<br>".join(_html.escape(line) for line in cell)
            parts.append(f"      <td>{content}</td>")
        parts.append("    </tr>")
    parts.append("  </tbody>")
    parts.append("</table>")
    return "\n".join(parts)


def tabulate(
    tabular_data: Any,
    headers: Union[Sequence[Any], str, None] = (),
    tablefmt: Union[str, SeparatedFormat] = "simple",
    floatfmt: str = "g",
    numalign: Optional[str] = "right",
    stralign: Optional[str] = "left",
    missingval: str = "",
    colalign: Optional[Sequence[Optional[str]]] = None,
) -> str:
    """
    Format tabular_data as a table.

    Parameters:
        tabular_data: list of lists, dict of columns, or list of dicts
        headers: sequence of headers, "firstrow", "keys", or None/()
        tablefmt: format name ("plain", "simple", "grid", "pipe", "tsv", "csv", "html"), or a SeparatedFormat via simple_separated_format
        floatfmt: format spec for floats (default "g")
        numalign: alignment for numeric cells: "left"/"right"/"center"/"decimal"
        stralign: alignment for string cells: "left"/"right"/"center"
        missingval: string to use for missing values (None)
        colalign: optional sequence of per-column alignment overrides ("left"/"center"/"right")
    """
    # Normalize headers default
    if headers == ():
        headers = None
    normalized_headers, rows = _normalize_tabular_data(tabular_data, headers, missingval)

    # If separated format (csv/tsv/custom), render early with minimal rules
    sep_format: Optional[SeparatedFormat] = None
    if isinstance(tablefmt, SeparatedFormat):
        sep_format = tablefmt
    else:
        if isinstance(tablefmt, str):
            lower = tablefmt.lower()
            if lower == "tsv":
                sep_format = SeparatedFormat(sep="\t", header=True, allow_padding=False)
            elif lower == "csv":
                sep_format = SeparatedFormat(sep=",", header=True, allow_padding=False)

    # Stringify
    headers_lines, rows_lines, rows_isnum = _stringify_table(rows, normalized_headers, floatfmt, missingval)

    # For separated, ignore alignment and padding; print as-is
    if sep_format is not None:
        return _render_separated(headers_lines, rows_lines, rows_isnum, sep_format.sep)

    # Default align if None
    numalign = ("right" if numalign is None else str(numalign)).lower()
    stralign = ("left" if stralign is None else str(stralign)).lower()
    # colalign accepted for 'pipe' header only; otherwise, individual cell alignment rules apply

    # Compute column widths
    widths = _compute_col_widths(headers_lines, rows_lines)

    # Apply colalign overrides by mapping textual "l/c/r" to names; they affect only how we pad when generating cells?
    # In this implementation, colalign is used for pipe header alignment row only.
    fmt_name = tablefmt.name if hasattr(tablefmt, "name") else (tablefmt.lower() if isinstance(tablefmt, str) else "")
    if isinstance(tablefmt, str):
        fmt_name = tablefmt.lower()
    else:
        # for separated formats handled above; for unknown objects, fallback to simple
        fmt_name = "simple"

    if fmt_name not in AVAILABLE_FORMATS and not isinstance(tablefmt, SeparatedFormat):
        # fallback
        fmt_name = "simple"

    if fmt_name == "plain":
        return _render_plain(headers_lines, rows_lines, rows_isnum, widths, numalign, stralign)
    elif fmt_name == "simple":
        return _render_simple(headers_lines, rows_lines, rows_isnum, widths, numalign, stralign)
    elif fmt_name == "grid":
        return _render_grid(headers_lines, rows_lines, rows_isnum, widths, numalign, stralign)
    elif fmt_name == "pipe":
        return _render_pipe(headers_lines, rows_lines, rows_isnum, widths, numalign, stralign, colalign=colalign)
    elif fmt_name == "html":
        return _render_html(headers_lines, rows_lines, rows_isnum)
    elif fmt_name in ("tsv", "csv"):
        # already handled as separated
        sep = "\t" if fmt_name == "tsv" else ","
        return _render_separated(headers_lines, rows_lines, rows_isnum, sep)
    else:
        # default to simple
        return _render_simple(headers_lines, rows_lines, rows_isnum, widths, numalign, stralign)
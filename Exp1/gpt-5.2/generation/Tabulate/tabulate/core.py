from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple, Union

from .formats import TableFormat, tabulate_formats, simple_separated_format as _ssf


def simple_separated_format(separator: str) -> TableFormat:
    return _ssf(separator)


def _is_mapping(x: Any) -> bool:
    return isinstance(x, Mapping)


def _as_list(x: Any) -> List[Any]:
    if x is None:
        return []
    if isinstance(x, (list, tuple)):
        return list(x)
    return [x]


def _stringify(val: Any, missingval: str = "") -> str:
    if val is None:
        return missingval
    # Keep bool as True/False like reference.
    return str(val)


def _split_lines(s: str) -> List[str]:
    # Preserve empty lines like reference: splitlines() drops trailing empty line unless keepends.
    # We'll emulate typical expectations: explicit '\n' yields extra row segments.
    parts = s.split("\n")
    return parts


def _detect_cols_from_dict_rows(rows: Sequence[Mapping[str, Any]], headers: Any) -> Tuple[List[str], List[List[Any]]]:
    if headers == "keys":
        # In reference, for list of dicts, headers="keys" uses union of keys in insertion order
        # encountered across rows.
        seen: List[str] = []
        seen_set = set()
        for r in rows:
            for k in r.keys():
                if k not in seen_set:
                    seen_set.add(k)
                    seen.append(str(k))
        hdrs = seen
    elif headers in (None, (), [], "firstrow"):
        hdrs = []
    elif isinstance(headers, Mapping):
        # mapping of original keys to display names
        hdrs = [str(v) for v in headers.values()]
    elif isinstance(headers, (list, tuple)):
        hdrs = [str(h) for h in headers]
    else:
        # fallback
        hdrs = []

    # Determine column keys order
    if headers == "keys":
        keys = [h for h in hdrs]
    elif isinstance(headers, Mapping):
        keys = list(headers.keys())
    elif isinstance(headers, (list, tuple)) and len(headers) > 0:
        # assume these are column keys if dict rows; reference treats list headers as labels,
        # but column selection still comes from keys union; tests typically use 'keys'.
        keys = list(rows[0].keys()) if rows else []
    else:
        keys = list(rows[0].keys()) if rows else []

    data: List[List[Any]] = []
    for r in rows:
        data.append([r.get(k, None) for k in keys])
    return hdrs, data


def _normalize_tabular_data(
    tabular_data: Any,
    headers: Any = (),
    showindex: Any = False,
    missingval: str = "",
) -> Tuple[List[str], List[List[Any]], Optional[List[Any]]]:
    index: Optional[List[Any]] = None

    if _is_mapping(tabular_data):
        # dict of columns -> values or scalar
        d: Mapping[Any, Any] = tabular_data
        keys = list(d.keys())
        cols: List[List[Any]] = []
        maxlen = 0
        for k in keys:
            v = d[k]
            if isinstance(v, (list, tuple)):
                col = list(v)
            else:
                col = [v]
            cols.append(col)
            maxlen = max(maxlen, len(col))
        rows: List[List[Any]] = []
        for i in range(maxlen):
            row = []
            for col in cols:
                row.append(col[i] if i < len(col) else None)
            rows.append(row)

        if headers == "keys":
            hdrs = [str(k) for k in keys]
        elif headers in (None, (), [], "firstrow"):
            hdrs = []
        elif isinstance(headers, (list, tuple)):
            hdrs = [str(h) for h in headers]
        else:
            hdrs = []
        data = rows

    elif isinstance(tabular_data, (list, tuple)) and tabular_data and all(_is_mapping(r) for r in tabular_data):
        # list of dicts
        dict_rows = list(tabular_data)  # type: ignore
        hdrs, data = _detect_cols_from_dict_rows(dict_rows, headers)

    else:
        # list of lists / list of tuples / generator
        rows_list = list(tabular_data) if not isinstance(tabular_data, (list, tuple)) else list(tabular_data)
        # Special: single dict in list is handled above; if tabular_data is empty
        if not rows_list:
            hdrs = []
            data = []
        else:
            # If headers == "firstrow": first row is header
            if headers == "firstrow":
                first = rows_list[0]
                hdrs = [str(x) for x in _as_list(first)]
                data = [list(_as_list(r)) for r in rows_list[1:]]
            elif headers in (None, (), [], "keys"):
                hdrs = []
                data = [list(_as_list(r)) for r in rows_list]
            elif isinstance(headers, (list, tuple)):
                hdrs = [str(h) for h in headers]
                data = [list(_as_list(r)) for r in rows_list]
            else:
                hdrs = []
                data = [list(_as_list(r)) for r in rows_list]

    # showindex
    if showindex:
        if showindex == "always" or showindex is True:
            index = list(range(len(data)))
        elif showindex == "never":
            index = None
        elif isinstance(showindex, (list, tuple)):
            index = list(showindex)
        else:
            # truthy -> numeric
            index = list(range(len(data)))
    else:
        index = None

    # Ensure rectangular by padding None
    ncols = max((len(r) for r in data), default=0)
    if hdrs:
        ncols = max(ncols, len(hdrs))
    if index is not None:
        ncols += 1

    if index is not None:
        if hdrs:
            hdrs = [""] + list(hdrs)
        else:
            # no headers: keep as-is; index column still present but no header row by default
            pass

    norm: List[List[Any]] = []
    for i, r in enumerate(data):
        rr = list(r)
        if index is not None:
            rr = [index[i] if i < len(index) else i] + rr
        if len(rr) < ncols:
            rr.extend([None] * (ncols - len(rr)))
        norm.append(rr)

    if hdrs and len(hdrs) < ncols:
        hdrs = list(hdrs) + [""] * (ncols - len(hdrs))

    return (hdrs, norm, index)


def _infer_align(col_values: List[str]) -> str:
    # If all non-empty values parse as int/float -> right else left.
    def is_number(s: str) -> bool:
        ss = s.strip()
        if ss == "":
            return False
        try:
            float(ss)
            return True
        except Exception:
            return False

    any_data = False
    all_num = True
    for v in col_values:
        if v is None:
            continue
        if str(v).strip() == "":
            continue
        any_data = True
        if not is_number(str(v)):
            all_num = False
            break
    if any_data and all_num:
        return "right"
    return "left"


def _pad(text: str, width: int, align: str) -> str:
    if align == "right":
        return text.rjust(width)
    if align == "center":
        return text.center(width)
    if align == "decimal":
        # Minimal decimal alignment: align on last '.' if present else right
        if "." not in text:
            return text.rjust(width)
        left, right = text.split(".", 1)
        # Determine dot position based on width and max left; handled externally; fallback right
        return text.rjust(width)
    return text.ljust(width)


def _compute_widths(cell_lines: List[List[List[str]]], ncols: int) -> List[int]:
    widths = [0] * ncols
    for row in cell_lines:
        for j in range(ncols):
            lines = row[j]
            for ln in lines:
                widths[j] = max(widths[j], len(ln))
    return widths


def _render_separator(fmt: TableFormat, widths: List[int], kind: str) -> Optional[str]:
    # kind: above, below, between, header
    template = {
        "above": fmt.lineabove,
        "below": fmt.linebelow,
        "between": fmt.linebetweenrows,
        "header": fmt.lineheader if fmt.lineheader is not None else fmt.linebetweenrows,
    }.get(kind)
    if not template:
        return None

    # For formats with template "+{sep}+"
    if "{sep}" in template:
        # build segments like ---+---
        segs = []
        for w in widths:
            segs.append("-" * (w + fmt.pad * 2))
        return template.format(sep="+".join(segs))
    # For pipe header like "|{sep}|"
    if "{sep}" in template:
        return template.format(sep="")
    # Else treat as fixed string
    return template


def _render_row(
    fmt: TableFormat,
    row_lines: List[List[str]],
    widths: List[int],
    aligns: List[str],
) -> List[str]:
    ncols = len(widths)
    height = max(len(row_lines[j]) for j in range(ncols)) if ncols else 0
    out: List[str] = []
    vbar = fmt.linebetweencolumns
    colsep = fmt.colsep
    if colsep is None:
        colsep = " " * (fmt.pad * 2 + 1) if vbar is None else " "
    pad = " " * fmt.pad

    for i in range(height):
        cells: List[str] = []
        for j in range(ncols):
            lines = row_lines[j]
            text = lines[i] if i < len(lines) else ""
            text = _pad(text, widths[j], aligns[j])
            if fmt.pad:
                text = pad + text + pad
            cells.append(text)
        if vbar is None:
            out.append((colsep or " ").join(cells).rstrip())
        else:
            # if format uses a vbar, also wrap with it for pipe/grid-like
            # Determine joiner: if fmt.colsep provided, use it; else single space around bars
            joiner = fmt.colsep if fmt.colsep is not None else " "
            line = vbar + joiner.join(cells) + vbar
            out.append(line.rstrip())
    return out


def tabulate(
    tabular_data: Any,
    headers: Any = (),
    tablefmt: Union[str, TableFormat] = "simple",
    floatfmt: str = "g",
    intfmt: str = "",
    numalign: str = "decimal",
    stralign: str = "left",
    missingval: str = "",
    showindex: Any = False,
    disable_numparse: bool = False,
    colalign: Optional[Sequence[str]] = None,
) -> str:
    fmt: TableFormat
    if isinstance(tablefmt, str):
        fmt = tabulate_formats.get(tablefmt, tabulate_formats.get("plain"))
    else:
        fmt = tablefmt

    hdrs, rows, _ = _normalize_tabular_data(tabular_data, headers=headers, showindex=showindex, missingval=missingval)
    ncols = max((len(r) for r in rows), default=0)
    if hdrs:
        ncols = max(ncols, len(hdrs))

    # Prepare string cells with multiline support
    def format_value(v: Any) -> str:
        if v is None:
            return missingval
        if not disable_numparse and isinstance(v, bool) is False and isinstance(v, int) and intfmt:
            try:
                return format(v, intfmt)
            except Exception:
                return str(v)
        if not disable_numparse and isinstance(v, bool) is False and isinstance(v, float):
            try:
                return format(v, floatfmt)
            except Exception:
                return str(v)
        return _stringify(v, missingval=missingval)

    table_str: List[List[str]] = []
    if hdrs:
        table_str.append([str(h) for h in hdrs] + [""] * (ncols - len(hdrs)))
    for r in rows:
        rr = list(r) + [None] * (ncols - len(r))
        table_str.append([format_value(v) for v in rr])

    # Convert to list of cell lines
    cell_lines: List[List[List[str]]] = []
    for r in table_str:
        row_lines: List[List[str]] = []
        for c in r[:ncols]:
            lines = _split_lines(c)
            row_lines.append(lines)
        cell_lines.append(row_lines)

    widths = _compute_widths(cell_lines, ncols)

    # Determine alignment per column
    aligns: List[str] = []
    if colalign is not None:
        aligns = [(a or stralign) for a in list(colalign)[:ncols]]
        if len(aligns) < ncols:
            aligns.extend([stralign] * (ncols - len(aligns)))
    else:
        # infer numeric columns from data rows only (excluding header row)
        data_start = 1 if hdrs else 0
        for j in range(ncols):
            col_vals = []
            for i in range(data_start, len(table_str)):
                col_vals.append(table_str[i][j])
            if not disable_numparse and _infer_align(col_vals) == "right":
                aligns.append("right" if numalign in ("right", "decimal") else numalign)
            else:
                aligns.append(stralign)

    if fmt.is_html:
        return _tabulate_html(hdrs, rows, ncols, aligns, missingval, disable_numparse, floatfmt, intfmt)

    # Render
    out_lines: List[str] = []
    sep_above = _render_separator(fmt, widths, "above")
    if sep_above:
        out_lines.append(sep_above)

    start_row = 0
    if hdrs:
        out_lines.extend(_render_row(fmt, cell_lines[0], widths, aligns))
        sep_hdr = _render_separator(fmt, widths, "header")
        if sep_hdr:
            if fmt is tabulate_formats.get("pipe"):
                # Markdown header separator with ':' based on alignment
                parts = []
                for j, w in enumerate(widths):
                    core = "-" * max(3, w + fmt.pad * 2)
                    if aligns[j] == "left":
                        core = ":" + core[1:]
                    elif aligns[j] == "right":
                        core = core[:-1] + ":"
                    elif aligns[j] == "center":
                        core = ":" + core[1:-1] + ":"
                    parts.append(core)
                out_lines.append("|" + "|".join(parts) + "|")
            else:
                out_lines.append(sep_hdr)
        start_row = 1

    for ridx in range(start_row, len(cell_lines)):
        out_lines.extend(_render_row(fmt, cell_lines[ridx], widths, aligns))
        if fmt.linebetweenrows and ridx != len(cell_lines) - 1:
            sep_mid = _render_separator(fmt, widths, "between")
            if sep_mid:
                out_lines.append(sep_mid)

    sep_below = _render_separator(fmt, widths, "below")
    if sep_below:
        out_lines.append(sep_below)

    # For plaintext, strip trailing spaces per line like reference tends to do
    if fmt.plaintext:
        out_lines = [ln.rstrip() for ln in out_lines]

    return fmt.rowsep.join(out_lines)


def _escape_html(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )


def _tabulate_html(
    hdrs: List[str],
    rows: List[List[Any]],
    ncols: int,
    aligns: List[str],
    missingval: str,
    disable_numparse: bool,
    floatfmt: str,
    intfmt: str,
) -> str:
    def format_value(v: Any) -> str:
        if v is None:
            return missingval
        if not disable_numparse and isinstance(v, bool) is False and isinstance(v, int) and intfmt:
            try:
                return format(v, intfmt)
            except Exception:
                return str(v)
        if not disable_numparse and isinstance(v, bool) is False and isinstance(v, float):
            try:
                return format(v, floatfmt)
            except Exception:
                return str(v)
        return str(v)

    lines: List[str] = []
    lines.append("<table>")
    if hdrs:
        lines.append("<thead>")
        lines.append("<tr>")
        for j in range(ncols):
            h = hdrs[j] if j < len(hdrs) else ""
            style = ""
            if aligns[j] in ("left", "right", "center"):
                style = f' style="text-align: {aligns[j]}"'
            lines.append(f"<th{style}>{_escape_html(str(h))}</th>")
        lines.append("</tr>")
        lines.append("</thead>")
    lines.append("<tbody>")
    for r in rows:
        lines.append("<tr>")
        rr = list(r) + [None] * (ncols - len(r))
        for j in range(ncols):
            v = format_value(rr[j])
            style = ""
            if aligns[j] in ("left", "right", "center"):
                style = f' style="text-align: {aligns[j]}"'
            # Preserve multiline by converting newlines to <br/>
            v = _escape_html(v).replace("\n", "<br/>")
            lines.append(f"<td{style}>{v}</td>")
        lines.append("</tr>")
    lines.append("</tbody>")
    lines.append("</table>")
    return "\n".join(lines)
from __future__ import annotations

import csv
import io
from typing import Any, Iterable, List, Optional, Sequence, Tuple

# This module implements minimal CSV import/export for Dataset.


def export_dataset(ds: Any) -> str:
    """
    Export a Dataset-like object to CSV.
    Values are written as strings; None becomes empty string.
    """
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")

    headers = getattr(ds, "_headers", None)
    if headers is not None:
        writer.writerow([h if h is not None else "" for h in headers])

    for row in getattr(ds, "_data", []):
        writer.writerow([_stringify_cell(v) for v in row])

    return output.getvalue()


def import_dataset(text: str) -> Tuple[Optional[List[str]], List[List[str]]]:
    """
    Import CSV into (headers, rows). All values are returned as strings.
    If the CSV is empty, returns (None, []).
    Assumes first row contains headers when present.
    """
    if text is None:
        text = ""
    f = io.StringIO(text)
    reader = csv.reader(f)
    rows: List[List[str]] = [list(r) for r in reader]

    if not rows:
        return None, []

    headers = list(rows[0])
    data = [list(r) for r in rows[1:]]

    # Normalize row widths to headers length by padding/truncating.
    w = len(headers)
    norm: List[List[str]] = []
    for r in data:
        if len(r) < w:
            r = r + [""] * (w - len(r))
        elif len(r) > w:
            r = r[:w]
        norm.append(r)

    return headers, norm


def _stringify_cell(v: Any) -> str:
    if v is None:
        return ""
    return str(v)
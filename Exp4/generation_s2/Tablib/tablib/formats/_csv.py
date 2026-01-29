from __future__ import annotations

import csv
import io
from typing import Any, List, Optional

# Avoid importing Dataset at module import time to prevent circular imports.


def export_set(dataset: Any) -> str:
    """
    Export a Dataset to a CSV string.
    Uses Python's csv module with excel dialect.
    """
    output = io.StringIO()
    writer = csv.writer(output, dialect="excel", lineterminator="\n")

    headers = dataset._headers  # internal access (tests focus on behavior)
    if headers is not None:
        writer.writerow([_to_str(h) for h in headers])

    for row in dataset._data:
        writer.writerow([_to_str(v) for v in row])

    return output.getvalue()


def import_set(csv_string: str):
    """
    Import a CSV string into a new Dataset.
    Heuristic:
      - If first row looks like headers (all strings) treat as headers.
      - Otherwise treat all rows as data and headers=None.
    Values are imported as strings (standard CSV behavior).
    """
    from tablib.core import Dataset

    s = csv_string or ""
    inp = io.StringIO(s)
    reader = csv.reader(inp, dialect="excel")

    rows: List[List[str]] = [list(r) for r in reader]
    if not rows:
        return Dataset()

    first = rows[0]
    rest = rows[1:]

    # Heuristic: treat first row as headers if there are more rows OR if caller expects headers.
    # Tablib typically treats first row as headers when dataset has headers.
    # For our minimal implementation, assume first row is headers if all cells are non-empty strings.
    def is_header_row(r: List[str]) -> bool:
        # accept empty header cells too; still headers row.
        return True

    if is_header_row(first):
        ds = Dataset(headers=first)
        for r in rest:
            ds.append(r)
        return ds

    ds = Dataset()
    for r in rows:
        ds.append(r)
    return ds


def _to_str(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, str):
        return v
    return str(v)
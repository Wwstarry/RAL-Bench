from __future__ import annotations

import csv
import io
from typing import Any, Iterable, List, Tuple


def export_dataset(dataset) -> str:
    """
    Export a Dataset to CSV.

    Includes headers if present and non-empty.
    Normalizes to dataset.width: missing values become empty, extras ignored.
    """
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")

    width = dataset.width

    if getattr(dataset, "headers", None):
        hdr = dataset.headers
        if hdr:
            row = []
            for i in range(width):
                v = hdr[i] if i < len(hdr) else ""
                row.append("" if v is None else str(v))
            writer.writerow(row)

    for r in dataset._data:
        row = []
        for i in range(width):
            v = r[i] if i < len(r) else None
            row.append("" if v is None else str(v))
        writer.writerow(row)

    return out.getvalue()


def import_dataset(dataset, text: str) -> None:
    """
    Import CSV into an existing Dataset, replacing its contents.

    Behavior: treat first row as headers (when present). Remaining rows are data.
    All values are imported as strings (empty string for missing cells).
    """
    s = io.StringIO(text or "")
    reader = csv.reader(s)

    rows: List[List[str]] = list(reader)
    if not rows:
        dataset._set_data(headers=[], rows=[], title=getattr(dataset, "title", None))
        return

    headers = rows[0]
    data_rows = rows[1:]

    # Keep row widths as-is; dataset width will follow headers length.
    dataset._set_data(headers=headers, rows=[tuple(r) for r in data_rows], title=getattr(dataset, "title", None))
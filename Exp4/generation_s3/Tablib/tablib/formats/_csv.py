from __future__ import annotations

import csv
import io
from typing import Any, List, Sequence


def export_dataset(dataset) -> str:
    """
    Export Dataset to CSV text.

    First row is headers. Values are written with the stdlib csv module.
    """
    output = io.StringIO(newline="")
    writer = csv.writer(output)

    headers = getattr(dataset, "headers", []) or []
    # Ensure headers align with dataset width if possible.
    width = getattr(dataset, "width", len(headers))
    if not headers and width:
        headers = [f"col{i}" for i in range(1, width + 1)]
    if headers:
        writer.writerow(list(headers))

    # Write rows
    for row in dataset[:]:
        # row is already tuple; normalize to width
        r = list(row)
        if width and len(r) < width:
            r.extend([None] * (width - len(r)))
        elif width and len(r) > width:
            r = r[:width]
        writer.writerow(r)

    return output.getvalue()


def import_dataset(dataset, csv_text: str) -> None:
    """
    Import CSV text into Dataset, replacing contents.

    First row treated as headers. Remaining rows are data rows.
    Empty input yields empty dataset.
    """
    text = csv_text or ""
    text = text.strip("\ufeff")  # tolerate BOM
    if not text.strip():
        dataset._set_data(headers=[], rows=[], title=getattr(dataset, "title", None))
        return

    f = io.StringIO(text, newline="")
    reader = csv.reader(f)

    rows: List[List[Any]] = []
    for r in reader:
        rows.append(list(r))

    if not rows:
        dataset._set_data(headers=[], rows=[], title=getattr(dataset, "title", None))
        return

    headers = [str(h) for h in rows[0]]
    data_rows: List[Sequence[Any]] = rows[1:]

    # Values remain strings as provided by csv.reader.
    dataset._set_data(headers=headers, rows=data_rows, title=getattr(dataset, "title", None))
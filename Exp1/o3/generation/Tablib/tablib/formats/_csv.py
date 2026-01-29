"""Very small CSV formatter for the subset Tablib clone."""

from __future__ import annotations

import csv
import io
from typing import List, Any

from ..core import Dataset


def export_set(dataset: Dataset) -> str:
    """Return dataset as CSV string (UTF-8)."""
    stream = io.StringIO()
    writer = csv.writer(stream)
    if dataset.headers:
        writer.writerow(dataset.headers)
    for row in dataset:
        writer.writerow(list(row))
    return stream.getvalue()


def import_set(dataset: Dataset, in_str: str):
    """Parse CSV *in_str* into *dataset* (in place)."""
    stream = io.StringIO(in_str)
    reader = csv.reader(stream)
    rows: List[List[Any]] = list(reader)
    if not rows:
        dataset._headers = None
        dataset._rows = []
        return

    dataset._headers = list(rows[0])
    dataset._rows = [list(r) for r in rows[1:]]
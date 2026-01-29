import csv
import io
from typing import Tuple, List, Optional, Iterable


def export_set(dataset) -> str:
    """Export a Dataset to CSV string."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    headers = dataset.headers
    w = dataset.width
    if headers is not None:
        writer.writerow([h if h is not None else "" for h in headers])
    for r in dataset._data:
        row = r
        # normalize to width
        if len(row) < w:
            row = list(row) + [None] * (w - len(row))
        elif len(row) > w:
            row = list(row[:w])
        # convert None to empty string for CSV
        writer.writerow(["" if x is None else x for x in row])
    return buf.getvalue()


def import_set(s: str) -> Tuple[Optional[List[str]], List[List[str]]]:
    """Import a Dataset from CSV string.

    Returns: (headers, rows)
    """
    if not s:
        return None, []
    buf = io.StringIO(s)
    reader = csv.reader(buf)
    rows = [row for row in reader]
    if not rows:
        return None, []
    headers = rows[0]
    data_rows = rows[1:]
    # Return rows as-is (strings); headers as list of strings
    return headers, data_rows
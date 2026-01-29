"""Very small JSON formatter for the subset Tablib clone."""

from __future__ import annotations

import json
from typing import List, Any

from ..core import Dataset


def export_set(dataset: Dataset) -> str:
    """Return dataset as a JSON string.

    Representation format:
        {
            "headers": [...],
            "data": [[row1], [row2], ...]
        }
    """
    payload = {
        "headers": dataset.headers,
        "data": [list(r) for r in dataset],
    }
    return json.dumps(payload)


def import_set(dataset: Dataset, in_str: str):
    """Populate *dataset* with the contents of *in_str* (JSON)."""
    raw = json.loads(in_str)
    headers = raw.get("headers")
    data: List[List[Any]] = raw.get("data", [])
    dataset._headers = list(headers) if headers is not None else None
    dataset._rows = [list(r) for r in data]
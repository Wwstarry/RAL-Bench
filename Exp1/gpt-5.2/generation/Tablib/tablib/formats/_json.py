from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple


def export_dataset(ds: Any) -> str:
    """
    Export Dataset to JSON.

    Shape is:
    {
      "headers": [...],   # null if no headers
      "data": [[...], ...]
    }
    """
    payload: Dict[str, Any] = {
        "headers": getattr(ds, "_headers", None),
        "data": getattr(ds, "_data", []),
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def import_dataset(text: str) -> Tuple[Optional[List[str]], List[List[Any]]]:
    if text is None or text == "":
        return None, []
    obj = json.loads(text)
    headers = obj.get("headers", None)
    data = obj.get("data", [])
    if headers is not None:
        headers = list(headers)
        w = len(headers)
        norm: List[List[Any]] = []
        for r in data:
            r = list(r)
            if len(r) < w:
                r = r + [None] * (w - len(r))
            elif len(r) > w:
                r = r[:w]
            norm.append(r)
        data = norm
    else:
        data = [list(r) for r in data]
    return headers, data


def export_book(book: Any) -> str:
    """
    Export Databook to JSON preserving sheet titles, headers and data.

    Shape:
    {
      "sheets": [
        {"title": "...", "headers": [...], "data": [[...], ...]},
        ...
      ]
    }
    """
    sheets = []
    for ds in book.sheets() if hasattr(book, "sheets") else list(book):
        sheets.append(
            {
                "title": getattr(ds, "title", None),
                "headers": getattr(ds, "_headers", None),
                "data": getattr(ds, "_data", []),
            }
        )
    return json.dumps({"sheets": sheets}, ensure_ascii=False, separators=(",", ":"))


def import_book(text: str) -> List[Any]:
    from tablib.core import Dataset  # local import to avoid circular

    if text is None or text == "":
        return []
    obj = json.loads(text)
    sheets = obj.get("sheets", [])
    datasets: List[Dataset] = []
    for sh in sheets:
        ds = Dataset(headers=sh.get("headers", None))
        ds.title = sh.get("title", None)
        data = sh.get("data", []) or []
        ds._data = [list(r) for r in data]
        # Normalize to header width if headers exist.
        if ds._headers is not None:
            w = len(ds._headers)
            norm = []
            for r in ds._data:
                if len(r) < w:
                    r = r + [None] * (w - len(r))
                elif len(r) > w:
                    r = r[:w]
                norm.append(r)
            ds._data = norm
        datasets.append(ds)
    return datasets
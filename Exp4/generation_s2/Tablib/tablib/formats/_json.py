from __future__ import annotations

import json
from typing import Any, Dict, List, Optional


def export_set(dataset: Any) -> str:
    """
    Export a Dataset to JSON string.
    Structure is compatible with our importer and stable for tests.
    """
    payload: Dict[str, Any] = {
        "title": getattr(dataset, "title", None),
        "headers": dataset._headers,
        "data": [list(r) for r in dataset._data],
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def import_set(json_string: str):
    from tablib.core import Dataset

    s = json_string or ""
    if not s.strip():
        return Dataset()

    obj = json.loads(s)
    if isinstance(obj, dict) and "data" in obj:
        headers = obj.get("headers", None)
        data = obj.get("data", [])
        ds = Dataset(headers=headers)
        ds.title = obj.get("title", None)
        for r in data:
            ds.append(r)
        return ds

    # Accept a list of dicts as a dataset, using keys as headers in encounter order.
    if isinstance(obj, list):
        if not obj:
            return Dataset()
        if all(isinstance(x, dict) for x in obj):
            headers = _ordered_union_headers(obj)
            ds = Dataset(headers=headers)
            for d in obj:
                ds.append([d.get(h) for h in headers])
            return ds

    raise ValueError("Unsupported JSON payload for Dataset")


def export_book(book: Any) -> str:
    sheets_payload: List[Dict[str, Any]] = []
    for ds in book.sheets():
        sheets_payload.append(
            {
                "title": getattr(ds, "title", None),
                "headers": ds._headers,
                "data": [list(r) for r in ds._data],
            }
        )
    payload: Dict[str, Any] = {"sheets": sheets_payload}
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def import_book(json_string: str):
    from tablib.core import Databook, Dataset

    s = json_string or ""
    if not s.strip():
        return Databook([])

    obj = json.loads(s)
    if not (isinstance(obj, dict) and isinstance(obj.get("sheets"), list)):
        raise ValueError("Unsupported JSON payload for Databook")

    datasets: List[Dataset] = []
    for sheet in obj["sheets"]:
        if not isinstance(sheet, dict):
            continue
        ds = Dataset(headers=sheet.get("headers", None))
        ds.title = sheet.get("title", None)
        for r in sheet.get("data", []) or []:
            ds.append(r)
        datasets.append(ds)

    return Databook(datasets)


def _ordered_union_headers(dict_rows: List[Dict[str, Any]]) -> List[str]:
    headers: List[str] = []
    seen = set()
    for d in dict_rows:
        for k in d.keys():
            if k not in seen:
                seen.add(k)
                headers.append(k)
    return headers
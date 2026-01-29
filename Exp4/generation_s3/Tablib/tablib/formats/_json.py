from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Sequence


def export_dataset(dataset) -> str:
    payload = {
        "title": getattr(dataset, "title", None),
        "headers": list(getattr(dataset, "headers", []) or []),
        "data": [list(r) for r in dataset[:]],
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def import_dataset(dataset, json_text: str) -> None:
    obj = json.loads(json_text or "null")
    if obj is None:
        dataset._set_data(headers=[], rows=[], title=getattr(dataset, "title", None))
        return
    if not isinstance(obj, dict):
        raise ValueError("Invalid dataset JSON: expected object")

    headers = obj.get("headers", [])
    data = obj.get("data", [])
    title = obj.get("title", None)

    if headers is None:
        headers = []
    if data is None:
        data = []

    if not isinstance(headers, list):
        raise ValueError("Invalid dataset JSON: headers must be a list")
    if not isinstance(data, list):
        raise ValueError("Invalid dataset JSON: data must be a list")

    dataset._set_data(headers=[str(h) for h in headers], rows=data, title=title)


def export_databook(book) -> str:
    sheets = []
    for ds in book.sheets():
        sheets.append(
            {
                "title": getattr(ds, "title", None),
                "headers": list(getattr(ds, "headers", []) or []),
                "data": [list(r) for r in ds[:]],
            }
        )
    payload = {"sheets": sheets}
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def import_databook(book, json_text: str) -> None:
    obj = json.loads(json_text or "null")
    if obj is None:
        book._set_sheets([])
        return
    if not isinstance(obj, dict):
        raise ValueError("Invalid databook JSON: expected object")

    sheets = obj.get("sheets", None)
    if sheets is None:
        raise ValueError("Invalid databook JSON: missing 'sheets'")
    if not isinstance(sheets, list):
        raise ValueError("Invalid databook JSON: 'sheets' must be a list")

    # Import locally to avoid circular import at module import time.
    from ..core import Dataset

    datasets: List[Dataset] = []
    for sheet in sheets:
        if not isinstance(sheet, dict):
            raise ValueError("Invalid databook JSON: sheet must be an object")
        title = sheet.get("title", None)
        headers = sheet.get("headers", [])
        data = sheet.get("data", [])

        if headers is None:
            headers = []
        if data is None:
            data = []

        if not isinstance(headers, list):
            raise ValueError("Invalid databook JSON: sheet headers must be a list")
        if not isinstance(data, list):
            raise ValueError("Invalid databook JSON: sheet data must be a list")

        ds = Dataset(headers=[str(h) for h in headers])
        ds.title = title
        for r in data:
            ds.append(r)
        datasets.append(ds)

    book._set_sheets(datasets)
from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


def _dataset_to_obj(dataset) -> Dict[str, Any]:
    width = dataset.width
    headers = list(dataset.headers) if getattr(dataset, "headers", None) else []
    title = getattr(dataset, "title", None)

    data: List[List[Any]] = []
    for r in dataset._data:
        row = []
        for i in range(width):
            row.append(r[i] if i < len(r) else None)
        data.append(row)

    return {
        "title": title,
        "headers": headers,
        "data": data,
    }


def export_dataset(dataset) -> str:
    obj = _dataset_to_obj(dataset)
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"), sort_keys=False)


def import_dataset(dataset, text: str) -> None:
    """
    Import JSON into an existing Dataset, replacing its contents.

    Supports two input shapes:
      1) {"title":..., "headers":[...], "data":[[...], ...]}
      2) [ {"col": value, ...}, ... ]  (list-of-dicts)
    """
    raw = json.loads(text or "null")
    title = getattr(dataset, "title", None)

    if raw is None:
        dataset._set_data(headers=[], rows=[], title=title)
        return

    if isinstance(raw, dict) and "data" in raw and "headers" in raw:
        headers = raw.get("headers") or []
        title = raw.get("title", title)
        data = raw.get("data") or []
        dataset._set_data(headers=headers, rows=[tuple(r) for r in data], title=title)
        return

    if isinstance(raw, list):
        # list-of-dicts fallback
        if not raw:
            dataset._set_data(headers=[], rows=[], title=title)
            return
        if not all(isinstance(x, dict) for x in raw):
            raise ValueError("Unsupported JSON dataset format")

        # Preserve insertion order of keys from the first row.
        headers = list(raw[0].keys())
        data_rows: List[List[Any]] = []
        for d in raw:
            row = [d.get(h, None) for h in headers]
            data_rows.append(row)
        dataset._set_data(headers=headers, rows=[tuple(r) for r in data_rows], title=title)
        return

    raise ValueError("Unsupported JSON dataset format")


def export_databook(book) -> str:
    datasets = []
    for ds in book.sheets():
        datasets.append(_dataset_to_obj(ds))
    obj = {"datasets": datasets}
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"), sort_keys=False)


def import_databook(book, text: str) -> None:
    raw = json.loads(text or "null")
    if raw is None:
        book._set_datasets([])
        return
    if not isinstance(raw, dict) or "datasets" not in raw:
        raise ValueError("Unsupported JSON databook format")

    sheets = raw.get("datasets") or []
    new_datasets = []
    for sheet in sheets:
        if not isinstance(sheet, dict):
            raise ValueError("Invalid dataset entry in databook JSON")
        headers = sheet.get("headers") or []
        data = sheet.get("data") or []
        title = sheet.get("title", None)
        from ..core import Dataset  # local import to avoid circular import at module load time

        ds = Dataset(headers=headers, title=title)
        # Directly set data for speed and to preserve None values.
        ds._set_data(headers=headers, rows=[tuple(r) for r in data], title=title)
        new_datasets.append(ds)

    book._set_datasets(new_datasets)
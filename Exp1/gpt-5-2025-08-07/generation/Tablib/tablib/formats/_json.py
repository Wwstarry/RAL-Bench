import json
from typing import Tuple, List, Optional, Any


def export_set(dataset) -> str:
    """Export a Dataset to JSON string.
    If headers exist, exports as list of objects keyed by headers.
    Otherwise, exports as list of lists.
    """
    headers = dataset.headers
    if headers is None:
        payload = [list(r) for r in dataset._data]
    else:
        w = dataset.width
        payload = []
        for r in dataset._data:
            # normalize to width
            row = list(r)
            if len(row) < w:
                row = row + [None] * (w - len(row))
            elif len(row) > w:
                row = row[:w]
            payload.append({str(headers[i]): row[i] for i in range(w)})
    return json.dumps(payload)


def import_set(s: str) -> Tuple[Optional[List[Any]], List[List[Any]]]:
    """Import a Dataset from JSON string (dataset-level).
    Accepts list of dicts (with headers) or list of lists.
    Returns: (headers, rows)
    """
    obj = json.loads(s) if s else []
    if obj is None or obj == []:
        return None, []
    if not isinstance(obj, list):
        raise ValueError("Dataset JSON must be a list")
    if len(obj) == 0:
        return None, []
    first = obj[0]
    # list of dicts
    if isinstance(first, dict):
        # derive headers from first object's keys in order
        # Python 3.7+ preserves insertion order
        headers = list(first.keys())
        rows: List[List[Any]] = []
        for item in obj:
            # ensure item is dict
            if not isinstance(item, dict):
                raise ValueError("Mixed types in dataset JSON")
            rows.append([item.get(h) for h in headers])
        return headers, rows
    else:
        # assume list of lists
        rows = []
        for item in obj:
            if not isinstance(item, list):
                raise ValueError("Mixed types in dataset JSON")
            rows.append(item)
        return None, rows


def export_book(book) -> str:
    """Export a Databook to JSON string."""
    sheets = []
    for ds in book.sheets():
        headers = ds.headers
        data = []
        w = ds.width
        for r in ds._data:
            row = list(r)
            if len(row) < w:
                row = row + [None] * (w - len(row))
            elif len(row) > w:
                row = row[:w]
            data.append(row)
        sheets.append({
            "title": ds.title,
            "headers": headers,
            "data": data,
        })
    payload = {"sheets": sheets}
    return json.dumps(payload)


def import_book(s: str) -> List[dict]:
    """Import a Databook from JSON string.
    Returns a list of sheet specifications: dicts with 'title', 'headers', and 'data'.
    """
    if not s:
        return []
    obj = json.loads(s)
    if not isinstance(obj, dict):
        raise ValueError("Databook JSON must be an object")
    sheets = obj.get("sheets", [])
    if not isinstance(sheets, list):
        raise ValueError("Databook JSON 'sheets' must be a list")
    out: List[dict] = []
    for sh in sheets:
        if not isinstance(sh, dict):
            raise ValueError("Invalid sheet entry")
        title = sh.get("title")
        headers = sh.get("headers")
        data = sh.get("data", [])
        if headers is not None and not isinstance(headers, list):
            raise ValueError("Invalid headers in sheet")
        if not isinstance(data, list):
            raise ValueError("Invalid data in sheet")
        out.append({"title": title, "headers": headers, "data": data})
    return out
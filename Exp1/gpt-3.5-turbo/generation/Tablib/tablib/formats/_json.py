import json

from ..core import Dataset, Databook


def export_set(dataset):
    # Export Dataset as JSON string
    # Format: {"title": title or null, "headers": [...], "rows": [[...], ...]}
    obj = {
        "title": dataset.title,
        "headers": dataset.headers,
        "rows": dataset._data,
    }
    return json.dumps(obj, separators=(',', ':'))


def import_set(json_string):
    obj = json.loads(json_string)
    headers = obj.get("headers", [])
    rows = obj.get("rows", [])
    ds = Dataset(*rows, headers=headers)
    ds.title = obj.get("title", None)
    return ds


def export_book(book):
    # Export Databook as JSON string
    # Format: {"sheets": [{"title":..., "headers":..., "rows":...}, ...]}
    sheets = []
    for ds in book.sheets():
        sheets.append({
            "title": ds.title,
            "headers": ds.headers,
            "rows": ds._data,
        })
    obj = {"sheets": sheets}
    return json.dumps(obj, separators=(',', ':'))


def import_book(json_string):
    obj = json.loads(json_string)
    sheets = obj.get("sheets", [])
    datasets = []
    for sheet in sheets:
        headers = sheet.get("headers", [])
        rows = sheet.get("rows", [])
        ds = Dataset(*rows, headers=headers)
        ds.title = sheet.get("title", None)
        datasets.append(ds)
    return Databook(datasets)
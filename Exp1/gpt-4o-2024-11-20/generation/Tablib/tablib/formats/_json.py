import json
from ..core import Dataset, Databook

def export_set(dataset):
    data = {
        "headers": dataset.headers,
        "rows": dataset._data
    }
    return json.dumps(data)

def import_set(json_string):
    data = json.loads(json_string)
    headers = data.get("headers", [])
    rows = data.get("rows", [])
    return Dataset(*rows, headers=headers)

def export_book(book):
    data = []
    for dataset in book.sheets():
        data.append({
            "title": getattr(dataset, "title", None),
            "headers": dataset.headers,
            "rows": dataset._data
        })
    return json.dumps(data)

def import_book(json_string):
    data = json.loads(json_string)
    datasets = []
    for sheet in data:
        dataset = Dataset(*sheet["rows"], headers=sheet["headers"])
        dataset.title = sheet.get("title")
        datasets.append(dataset)
    return Databook(datasets)
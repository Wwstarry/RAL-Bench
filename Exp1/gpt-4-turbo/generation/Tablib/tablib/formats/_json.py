import json
from ..core import Dataset, Databook

def export_set(dataset):
    # Export as list of dicts if headers exist, else as list of lists
    if dataset.headers is not None:
        data = dataset.dict
    else:
        data = [list(row) for row in dataset]
    return json.dumps({
        'headers': dataset.headers,
        'title': getattr(dataset, 'title', None),
        'data': data
    })

def import_set(json_string):
    obj = json.loads(json_string)
    headers = obj.get('headers')
    data = obj.get('data', [])
    ds = Dataset(headers=headers)
    for row in data:
        if headers is not None and isinstance(row, dict):
            # Dict mapping header to value
            ds.append([row.get(h) for h in headers])
        else:
            ds.append(row)
    ds.title = obj.get('title')
    return ds

def export_book(book):
    sheets = []
    for ds in book.sheets():
        sheets.append({
            'title': getattr(ds, 'title', None),
            'headers': ds.headers,
            'data': ds.dict
        })
    return json.dumps({'sheets': sheets})

def import_book(json_string):
    obj = json.loads(json_string)
    sheets = obj.get('sheets', [])
    datasets = []
    for sheet in sheets:
        headers = sheet.get('headers')
        data = sheet.get('data', [])
        ds = Dataset(headers=headers)
        for row in data:
            if headers is not None and isinstance(row, dict):
                ds.append([row.get(h) for h in headers])
            else:
                ds.append(row)
        ds.title = sheet.get('title')
        datasets.append(ds)
    return Databook(datasets)
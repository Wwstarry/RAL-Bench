import json

def export_set(dataset):
    return json.dumps(dataset.dict)

def import_set(dataset, in_stream):
    dataset.wipe()
    data = json.loads(in_stream)
    if not data:
        return
    
    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
        dataset.headers = list(data[0].keys())
        for row in data:
            dataset.append(list(row.values()))

def export_book(databook):
    books = []
    for sheet in databook.sheets():
        books.append({
            'title': sheet.title,
            'data': sheet.dict
        })
    return json.dumps(books)

def import_book(databook, in_stream):
    from tablib.core import Dataset
    databook.wipe()
    data = json.loads(in_stream)
    
    for sheet_data in data:
        ds = Dataset()
        ds.title = sheet_data.get('title')
        rows = sheet_data.get('data')
        if rows:
            if len(rows) > 0:
                ds.headers = list(rows[0].keys())
                for r in rows:
                    ds.append(list(r.values()))
        databook.add_sheet(ds)
import json
from tablib.core import Dataset, Databook

def export_set(dataset):
    """Export Dataset to JSON string."""
    data = dataset.dict
    return json.dumps(data)

def import_set(json_string):
    """Import JSON string to headers and data."""
    data = json.loads(json_string)
    headers = []
    rows = []
    
    if data and isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
        headers = list(data[0].keys())
        rows = [tuple(row.get(header, '') for header in headers) for row in data]
    
    return headers, rows

def export_book(databook):
    """Export Databook to JSON string."""
    book_data = []
    
    for dataset in databook:
        sheet_data = {
            'title': getattr(dataset, 'title', 'Sheet 1'),
            'headers': dataset.headers,
            'data': [list(row) for row in dataset]
        }
        book_data.append(sheet_data)
    
    return json.dumps(book_data)

def import_book(json_string):
    """Import JSON string to a list of Dataset objects."""
    book_data = json.loads(json_string)
    datasets = []
    
    for sheet_data in book_data:
        dataset = Dataset(*sheet_data.get('data', []), headers=sheet_data.get('headers', []))
        if 'title' in sheet_data:
            dataset.title = sheet_data['title']
        datasets.append(dataset)
    
    return datasets
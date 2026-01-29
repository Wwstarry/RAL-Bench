# -*- coding: utf-8 -*-

import json

title = 'json'

def _import_set_from_list_of_dicts(dataset, data):
    """Helper to populate a dataset from a list of dicts."""
    if not isinstance(data, list) or not data:
        return

    if isinstance(data[0], dict):
        headers = list(data[0].keys())
        dataset.headers = headers
        for row_dict in data:
            row = [row_dict.get(h) for h in headers]
            dataset.append(row)

def export_set(dataset):
    """Returns JSON representation of a Dataset."""
    return json.dumps(dataset.dict)

def import_set(dataset, in_stream):
    """Populates a Dataset from a JSON stream."""
    dataset.wipe()
    try:
        data = json.loads(in_stream)
    except json.JSONDecodeError:
        data = []
    _import_set_from_list_of_dicts(dataset, data)

def export_book(databook):
    """Returns JSON representation of a Databook."""
    book_list = []
    for sheet in databook.sheets():
        sheet_data = {
            'title': sheet.title,
            'data': sheet.dict
        }
        book_list.append(sheet_data)
    return json.dumps(book_list)

def import_book(databook, in_stream):
    """Populates a Databook from a JSON stream."""
    from ..core import Dataset  # Lazy import to prevent circular dependency

    databook.wipe()
    try:
        book_data = json.loads(in_stream)
    except json.JSONDecodeError:
        return

    if not isinstance(book_data, list):
        return

    for sheet_data in book_data:
        if not isinstance(sheet_data, dict):
            continue

        dataset = Dataset()
        dataset.title = sheet_data.get('title')
        
        data_list = sheet_data.get('data', [])
        _import_set_from_list_of_dicts(dataset, data_list)
        
        databook.add_sheet(dataset)
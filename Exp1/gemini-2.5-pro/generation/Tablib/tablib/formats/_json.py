import json

def export_set(dataset):
    """Returns JSON representation of Dataset."""
    return json.dumps(dataset.dict)

def import_set(dataset, in_stream):
    """Loads JSON data into the given Dataset."""
    try:
        data = json.loads(in_stream)
    except json.JSONDecodeError:
        data = []
    
    dataset._load_from_dict_list(data)

def export_book(databook):
    """Returns JSON representation of Databook."""
    book_dict = []
    for sheet in databook.sheets():
        sheet_dict = {
            'title': sheet.title,
            'data': sheet.dict
        }
        book_dict.append(sheet_dict)
    return json.dumps(book_dict)

def import_book(databook, in_stream):
    """Loads JSON data into the given Databook."""
    from ..core import Dataset

    try:
        sheets_data = json.loads(in_stream)
    except json.JSONDecodeError:
        sheets_data = []

    databook._sheets = []

    if not isinstance(sheets_data, list):
        return

    for sheet_data in sheets_data:
        if not isinstance(sheet_data, dict):
            continue

        new_sheet = Dataset()
        new_sheet.title = sheet_data.get('title')
        
        data_list = sheet_data.get('data', [])
        if isinstance(data_list, list):
            new_sheet._load_from_dict_list(data_list)
        
        databook._sheets.append(new_sheet)
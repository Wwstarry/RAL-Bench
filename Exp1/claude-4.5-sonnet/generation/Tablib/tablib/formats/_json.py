"""JSON format support."""

import json


def export_set(dataset):
    """Export a Dataset to JSON format.
    
    Args:
        dataset: A Dataset instance
        
    Returns:
        JSON string
    """
    # Export as list of dictionaries
    data = dataset.dict
    return json.dumps(data, indent=2)


def import_set(dataset, content):
    """Import JSON content into a Dataset.
    
    Args:
        dataset: A Dataset instance to populate
        content: JSON string (list of dicts)
    """
    # Clear existing data
    dataset._data = []
    dataset._headers = None
    
    # Parse JSON
    data = json.loads(content)
    
    if not data:
        return
    
    if not isinstance(data, list):
        raise ValueError("JSON must be a list of objects")
    
    # Extract headers from first object
    if data and isinstance(data[0], dict):
        dataset.headers = list(data[0].keys())
        
        # Add rows
        for obj in data:
            if isinstance(obj, dict):
                row = [obj.get(h) for h in dataset.headers]
                dataset.append(row)


def export_book(databook):
    """Export a Databook to JSON format.
    
    Args:
        databook: A Databook instance
        
    Returns:
        JSON string
    """
    sheets = []
    
    for dataset in databook.sheets():
        sheet_data = {
            'title': getattr(dataset, 'title', None),
            'headers': dataset.headers,
            'data': [list(row) for row in dataset._data]
        }
        sheets.append(sheet_data)
    
    return json.dumps(sheets, indent=2)


def import_book(databook, content):
    """Import JSON content into a Databook.
    
    Args:
        databook: A Databook instance to populate
        content: JSON string (list of sheet objects)
    """
    from tablib.core import Dataset
    
    # Clear existing datasets
    databook._datasets = []
    
    # Parse JSON
    sheets = json.loads(content)
    
    if not isinstance(sheets, list):
        raise ValueError("JSON must be a list of sheets")
    
    # Create datasets from sheets
    for sheet_data in sheets:
        dataset = Dataset()
        
        # Set title if present
        if 'title' in sheet_data and sheet_data['title']:
            dataset.title = sheet_data['title']
        
        # Set headers if present
        if 'headers' in sheet_data and sheet_data['headers']:
            dataset.headers = sheet_data['headers']
        
        # Add data rows
        if 'data' in sheet_data:
            for row in sheet_data['data']:
                dataset.append(row)
        
        databook._datasets.append(dataset)
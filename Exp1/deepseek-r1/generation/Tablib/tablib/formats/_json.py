"""JSON format support."""
import json
from typing import Any, Dict, List
from ..core import Dataset, Databook


def export_json(dataset: Dataset) -> str:
    """Export dataset to JSON string."""
    return json.dumps(dataset.dict, indent=2)


def import_json(json_string: str) -> Dataset:
    """Import dataset from JSON string."""
    data = json.loads(json_string)
    
    if not data:
        return Dataset()
    
    # Handle list of dictionaries
    if isinstance(data, list):
        if not data:
            return Dataset()
        
        # Get headers from first dict keys
        first_row = data[0]
        if isinstance(first_row, dict):
            headers = list(first_row.keys())
            rows = []
            for item in data:
                if isinstance(item, dict):
                    row = [item.get(header, '') for header in headers]
                    rows.append(row)
                else:
                    # Handle mixed data (shouldn't happen in valid export)
                    rows.append([str(item)])
            return Dataset(*rows, headers=headers)
        else:
            # List of lists or values
            return Dataset(*data)
    
    # Single dictionary
    elif isinstance(data, dict):
        headers = list(data.keys())
        # Check if values are lists (column-wise)
        if all(isinstance(v, list) for v in data.values()):
            # Column-wise format
            # Transpose to row-wise
            rows = []
            col_lengths = [len(v) for v in data.values()]
            if col_lengths:
                max_len = max(col_lengths)
                for i in range(max_len):
                    row = []
                    for header in headers:
                        col_values = data[header]
                        row.append(col_values[i] if i < len(col_values) else '')
                    rows.append(row)
            return Dataset(*rows, headers=headers)
        else:
            # Single row
            return Dataset([list(data.values())], headers=headers)
    
    # Scalar or other
    return Dataset([[str(data)]])


def export_book_json(databook: Databook) -> str:
    """Export databook to JSON string."""
    book_data = []
    for sheet in databook.sheets():
        sheet_data = {
            'title': getattr(sheet, 'title', f'Sheet{len(book_data) + 1}'),
            'headers': sheet.headers,
            'data': sheet._data
        }
        book_data.append(sheet_data)
    
    return json.dumps(book_data, indent=2)


def import_book_json(json_string: str) -> Databook:
    """Import databook from JSON string."""
    book_data = json.loads(json_string)
    
    if not isinstance(book_data, list):
        raise ValueError("Invalid databook JSON format")
    
    databook = Databook()
    for sheet_info in book_data:
        if not isinstance(sheet_info, dict):
            continue
            
        title = sheet_info.get('title', '')
        headers = sheet_info.get('headers', [])
        data = sheet_info.get('data', [])
        
        ds = Dataset(*data, headers=headers)
        ds.title = title
        databook.add_sheet(ds)
    
    return databook
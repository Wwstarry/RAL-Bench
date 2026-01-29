"""
JSON format support for tablib.
"""

import json
from tablib.core import Dataset


def export_json(dataset):
    """
    Export a Dataset to JSON format.

    Args:
        dataset: A Dataset instance.

    Returns:
        A JSON string.
    """
    data = {
        "headers": dataset.headers,
        "data": [list(row) for row in dataset._data],
    }
    return json.dumps(data)


def import_json(json_string):
    """
    Import a JSON string into a Dataset.

    Args:
        json_string: A JSON formatted string.

    Returns:
        A Dataset instance.
    """
    data = json.loads(json_string)
    headers = data.get("headers", [])
    rows = data.get("data", [])

    dataset = Dataset(*rows, headers=headers)
    return dataset


def export_databook_json(databook):
    """
    Export a Databook to JSON format.

    Args:
        databook: A Databook instance.

    Returns:
        A JSON string.
    """
    sheets = []
    for sheet in databook._sheets:
        sheet_data = {
            "title": sheet.title,
            "headers": sheet.headers,
            "data": [list(row) for row in sheet._data],
        }
        sheets.append(sheet_data)

    return json.dumps({"sheets": sheets})


def import_databook_json(json_string):
    """
    Import a JSON string into a Databook.

    Args:
        json_string: A JSON formatted string.

    Returns:
        A Databook instance.
    """
    from tablib.core import Databook

    data = json.loads(json_string)
    sheets_data = data.get("sheets", [])

    datasets = []
    for sheet_data in sheets_data:
        title = sheet_data.get("title")
        headers = sheet_data.get("headers", [])
        rows = sheet_data.get("data", [])

        dataset = Dataset(*rows, headers=headers)
        dataset.title = title
        datasets.append(dataset)

    return Databook(datasets)
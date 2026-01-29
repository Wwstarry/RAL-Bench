import json

def export_set(dataset):
    """
    Export a single Dataset to JSON.
    The structure used here is:
    {
      "headers": [...],
      "data": [
        [...],
        ...
      ]
    }
    """
    output = {
        "title": dataset.title,
        "headers": dataset.headers,
        "data": [[str(item) for item in row] for row in dataset._data]
    }
    return json.dumps(output)

def import_set(dataset, json_str):
    """
    Overwrite a single Dataset from JSON (matching the structure above).
    """
    parsed = json.loads(json_str)

    dataset._headers.clear()
    dataset._data.clear()

    dataset.title = parsed.get("title", None)
    dataset.headers = parsed.get("headers", [])

    for row in parsed.get("data", []):
        dataset.append(row)

def export_book(databook):
    """
    Export an entire Databook (list of Datasets) to JSON.
    The structure is a list of objects, each with:
      {
        "title": ...,
        "headers": [...],
        "data": [...]
      }
    """
    output = []
    for ds in databook.sheets():
        output.append({
            "title": ds.title,
            "headers": ds.headers,
            "data": [[str(item) for item in row] for row in ds._data],
        })
    return json.dumps(output)

def import_book(databook, json_str):
    """
    Overwrite an entire Databook from JSON in the given structure.
    """
    parsed = json.loads(json_str)

    # clear existing
    databook._datasets.clear()

    for ds_info in parsed:
        from ..core import Dataset
        ds = Dataset()
        ds.title = ds_info.get("title", None)
        ds.headers = ds_info.get("headers", [])
        for row in ds_info.get("data", []):
            ds.append(row)
        databook._datasets.append(ds)
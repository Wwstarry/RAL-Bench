import csv
from io import StringIO
from ..core import Dataset

def export_set(dataset):
    output = StringIO()
    writer = csv.writer(output)
    if dataset.headers:
        writer.writerow(dataset.headers)
    writer.writerows(dataset._data)
    return output.getvalue()

def import_set(csv_string):
    input_stream = StringIO(csv_string)
    reader = csv.reader(input_stream)
    rows = list(reader)
    headers = rows.pop(0) if rows else []
    return Dataset(*rows, headers=headers)
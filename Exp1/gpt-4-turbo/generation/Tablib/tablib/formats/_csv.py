import csv
import io
from ..core import Dataset

def export_set(dataset):
    output = io.StringIO()
    writer = csv.writer(output)
    if dataset.headers is not None:
        writer.writerow(dataset.headers)
    for row in dataset:
        writer.writerow(row)
    return output.getvalue()

def import_set(csv_string):
    input_ = io.StringIO(csv_string)
    reader = csv.reader(input_)
    rows = list(reader)
    if not rows:
        return Dataset()
    # If first row looks like headers, treat as headers
    headers = rows[0]
    data_rows = rows[1:]
    ds = Dataset(headers=headers)
    for row in data_rows:
        ds.append(row)
    return ds
import csv
import io

from ..core import Dataset


def export_set(dataset):
    # dataset: Dataset instance
    output = io.StringIO()
    writer = csv.writer(output, lineterminator='\n')
    if dataset.headers:
        writer.writerow(dataset.headers)
    for row in dataset._data:
        writer.writerow(row)
    return output.getvalue()


def import_set(csv_string):
    input_io = io.StringIO(csv_string)
    reader = csv.reader(input_io)
    rows = list(reader)
    if not rows:
        # empty dataset
        return Dataset()
    headers = rows[0]
    data_rows = rows[1:]
    ds = Dataset(*data_rows, headers=headers)
    return ds
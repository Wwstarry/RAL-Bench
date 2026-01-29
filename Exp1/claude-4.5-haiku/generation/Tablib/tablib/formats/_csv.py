"""
CSV format support for tablib.
"""

import csv
from io import StringIO
from tablib.core import Dataset


def export_csv(dataset):
    """
    Export a Dataset to CSV format.

    Args:
        dataset: A Dataset instance.

    Returns:
        A CSV string.
    """
    output = StringIO()
    writer = csv.writer(output)

    # Write headers if present
    if dataset.headers:
        writer.writerow(dataset.headers)

    # Write data rows
    for row in dataset._data:
        writer.writerow(row)

    return output.getvalue()


def import_csv(csv_string):
    """
    Import a CSV string into a Dataset.

    Args:
        csv_string: A CSV formatted string.

    Returns:
        A Dataset instance.
    """
    reader = csv.reader(StringIO(csv_string))
    rows = list(reader)

    if not rows:
        return Dataset(headers=[])

    # First row is headers
    headers = rows[0]
    data_rows = rows[1:]

    dataset = Dataset(*data_rows, headers=headers)
    return dataset
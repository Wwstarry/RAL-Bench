# -*- coding: utf-8 -*-

import csv
import io

title = 'csv'

def export_set(dataset):
    """Returns CSV representation of a Dataset."""
    stream = io.StringIO()
    writer = csv.writer(stream)

    if dataset.headers:
        writer.writerow(dataset.headers)

    for row in dataset:
        writer.writerow(row)

    return stream.getvalue()

def import_set(dataset, in_stream):
    """Populates a Dataset from a CSV stream."""
    dataset.wipe()
    stream = io.StringIO(in_stream)
    reader = csv.reader(stream)

    try:
        headers = next(reader)
        dataset.headers = headers
        for row in reader:
            # Pad rows that are shorter than headers
            if len(row) < len(headers):
                row.extend([None] * (len(headers) - len(row)))
            # Truncate rows that are longer than headers
            elif len(row) > len(headers):
                row = row[:len(headers)]
            dataset.append(row)
    except StopIteration:
        # This occurs with an empty file
        pass
import csv
import io

def export_set(dataset):
    """Returns CSV representation of Dataset."""
    stream = io.StringIO()
    writer = csv.writer(stream, lineterminator='\n')

    if dataset.headers:
        writer.writerow(dataset.headers)

    for row in dataset._data:
        writer.writerow(row)

    return stream.getvalue()

def import_set(dataset, in_stream):
    """Loads CSV data into the given Dataset."""
    stream = io.StringIO(in_stream)
    reader = csv.reader(stream)

    dataset.wipe()

    try:
        headers = next(reader)
        dataset.headers = headers
        for row in reader:
            dataset.append(row)
    except StopIteration:
        # This handles empty files
        pass
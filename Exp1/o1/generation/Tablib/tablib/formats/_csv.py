import io
import csv


def export_set(dataset):
    """
    Return CSV string for a single Dataset object.
    Headers (if present) are written as the first row.
    """
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")

    if dataset.headers:
        writer.writerow(dataset.headers)

    for row in dataset._data:
        # Coerce all values to string
        writer.writerow([str(x) for x in row])

    return output.getvalue()


def import_set(dataset, in_stream):
    """
    Overwrite a Dataset object's content from a CSV string.
    Assumes the first row is headers.
    """
    # clear existing dataset
    dataset._headers.clear()
    dataset._data.clear()

    input_io = io.StringIO(in_stream)
    reader = csv.reader(input_io)

    rows = list(reader)
    if not rows:
        return

    # first row is headers
    dataset.headers = rows[0]

    # remaining are data
    for row in rows[1:]:
        dataset.append(row)
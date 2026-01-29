import csv
import io

def export_set(dataset):
    stream = io.StringIO()
    writer = csv.writer(stream)
    if dataset.headers:
        writer.writerow(dataset.headers)
    for row in dataset:
        writer.writerow(row)
    return stream.getvalue()

def import_set(dataset, in_stream):
    dataset.wipe()
    stream = io.StringIO(in_stream)
    reader = csv.reader(stream)
    try:
        headers = next(reader)
        dataset.headers = headers
    except StopIteration:
        pass
    
    for row in reader:
        dataset.append(row)
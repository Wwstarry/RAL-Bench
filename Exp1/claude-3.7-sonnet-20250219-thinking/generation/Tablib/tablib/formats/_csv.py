import csv
import io

def export_set(dataset):
    """Export Dataset to CSV string."""
    stream = io.StringIO()
    writer = csv.writer(stream, lineterminator='\n')
    
    if dataset.headers:
        writer.writerow(dataset.headers)
    
    for row in dataset:
        writer.writerow(row)
    
    return stream.getvalue()

def import_set(csv_string):
    """Import CSV string to headers and data."""
    stream = io.StringIO(csv_string)
    reader = csv.reader(stream)
    
    data = list(reader)
    headers = []
    rows = []
    
    if data:
        headers = data[0]
        rows = [tuple(row) for row in data[1:]]
    
    return headers, rows
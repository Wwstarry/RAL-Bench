"""CSV format support."""
import csv
import io
from typing import List
from ..core import Dataset


def export_csv(dataset: Dataset) -> str:
    """Export dataset to CSV string."""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write headers if present
    if dataset.headers:
        writer.writerow(dataset.headers)
    
    # Write data rows
    for row in dataset._data:
        writer.writerow(row)
    
    return output.getvalue()


def import_csv(csv_string: str) -> Dataset:
    """Import dataset from CSV string."""
    input_file = io.StringIO(csv_string)
    reader = csv.reader(input_file)
    
    rows = []
    headers = []
    
    # Try to read first row as headers
    try:
        first_row = next(reader)
    except StopIteration:
        # Empty CSV
        return Dataset()
    
    # Check if first row looks like headers (all strings, not empty)
    # For simplicity, we'll always treat first row as headers
    headers = [str(cell) for cell in first_row]
    
    # Read remaining rows
    for row in reader:
        rows.append(row)
    
    # Create dataset
    ds = Dataset(*rows, headers=headers)
    return ds
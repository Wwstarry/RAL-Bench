"""CSV format support."""

import csv
import io


def export_set(dataset):
    """Export a Dataset to CSV format.
    
    Args:
        dataset: A Dataset instance
        
    Returns:
        CSV string
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write headers if present
    if dataset.headers:
        writer.writerow(dataset.headers)
    
    # Write data rows
    for row in dataset._data:
        writer.writerow(row)
    
    return output.getvalue()


def import_set(dataset, content):
    """Import CSV content into a Dataset.
    
    Args:
        dataset: A Dataset instance to populate
        content: CSV string
    """
    # Clear existing data
    dataset._data = []
    dataset._headers = None
    
    # Parse CSV
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    
    if not rows:
        return
    
    # First row is headers
    if rows:
        dataset.headers = rows[0]
        
        # Remaining rows are data
        for row in rows[1:]:
            dataset.append(row)
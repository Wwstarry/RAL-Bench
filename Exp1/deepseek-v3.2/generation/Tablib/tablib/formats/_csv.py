"""CSV format support."""
import csv
import io


def import_set(dset, in_stream):
    """Import CSV data into dataset."""
    dset.csv = in_stream.read()


def export_set(dset):
    """Export dataset to CSV."""
    return dset.csv


def detect(stream):
    """Detect if stream contains CSV data."""
    try:
        # Try to read as CSV
        stream.seek(0)
        csv.Sniffer().sniff(stream.read(1024))
        stream.seek(0)
        return True
    except:
        return False
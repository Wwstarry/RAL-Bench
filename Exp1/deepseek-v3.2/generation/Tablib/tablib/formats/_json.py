"""JSON format support."""
import json


def import_set(dset, in_stream):
    """Import JSON data into dataset."""
    dset.json = in_stream.read()


def export_set(dset):
    """Export dataset to JSON."""
    return dset.json


def import_book(dbook, in_stream):
    """Import JSON data into databook."""
    dbook.json = in_stream.read()


def export_book(dbook):
    """Export databook to JSON."""
    return dbook.json


def detect(stream):
    """Detect if stream contains JSON data."""
    try:
        stream.seek(0)
        json.load(stream)
        stream.seek(0)
        return True
    except:
        return False
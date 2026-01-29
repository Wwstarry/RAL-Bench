# petl/transform/sort.py

def sort(table, field):
    """
    Sort the table by a specific field. This is a materializing operation.
    """
    it = iter(table)
    try:
        header = tuple(next(it))
    except StopIteration:
        return

    try:
        field_index = header.index(field)
    except ValueError:
        raise ValueError(f"Field not found: {repr(field)}")

    # Materialize the data rows
    data = list(it)

    # Sort in place based on the key
    data.sort(key=lambda row: row[field_index])

    # Yield results from the sorted data
    yield header
    yield from data
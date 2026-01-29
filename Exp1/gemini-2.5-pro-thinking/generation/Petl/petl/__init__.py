# petl/__init__.py

from .io.csv import fromcsv, tocsv
from .transform.conversions import convert, addfield
from .transform.selects import select, selectge, selectgt
from .transform.sort import sort
from .transform.joins import join

def fromdicts(records, header=None):
    """
    Construct a table from an iterable of dictionaries.
    """
    records_iterator = iter(records)

    try:
        first_record = next(records_iterator)
    except StopIteration:
        if header:
            yield tuple(header)
        return

    if header is None:
        # In Python 3.7+ dicts preserve insertion order.
        header = tuple(first_record.keys())

    yield header

    # Yield the first record's values
    yield tuple(first_record[h] for h in header)

    # Yield the rest
    for record in records_iterator:
        yield tuple(record[h] for h in header)
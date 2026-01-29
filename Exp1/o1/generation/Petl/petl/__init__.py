import os
from .io.csv import fromcsv, tocsv
from .transform.conversions import convert, addfield
from .transform.selects import select, selectge, selectgt
from .transform.sort import sort
from .transform.joins import join

__all__ = [
    'fromcsv',
    'tocsv',
    'fromdicts',
    'convert',
    'select',
    'selectge',
    'selectgt',
    'sort',
    'addfield',
    'join'
]

def fromdicts(records, header=None):
    """
    Create a lazy table from a list of dictionaries. 
    The 'header' argument can be provided to specify the columns;
    if omitted or None, an ordered union of all dict keys will be used.
    """
    return _FromDicts(records, header)

class _FromDicts:
    def __init__(self, records, header):
        self.records = records
        self._header = header
        self._resolved_header = None

    def __iter__(self):
        # Resolve header dynamically if not provided
        if self._header is not None:
            resolved_header = self._header
        else:
            # Gather all keys from all records in the order they appear
            seen = []
            for d in self.records:
                for k in d.keys():
                    if k not in seen:
                        seen.append(k)
            resolved_header = seen
        self._resolved_header = resolved_header

        yield resolved_header

        # Yield each record
        for d in self.records:
            row = [d.get(h, None) for h in resolved_header]
            yield row
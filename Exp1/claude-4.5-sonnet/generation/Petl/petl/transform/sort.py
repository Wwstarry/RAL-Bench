"""
Sorting operations.
"""


class SortTable:
    """Lazy table that sorts rows by a field."""
    
    def __init__(self, source, field):
        self.source = source
        self.field = field
    
    def __iter__(self):
        it = iter(self.source)
        header = next(it)
        yield header
        
        # Find the index of the sort field
        try:
            field_idx = header.index(self.field)
        except ValueError:
            raise ValueError(f"Field '{self.field}' not found in header")
        
        # Materialize and sort all rows
        rows = list(it)
        rows.sort(key=lambda row: row[field_idx])
        
        for row in rows:
            yield row


def sort(table, field):
    """
    Sort table by a field.
    
    Returns a lazy table wrapper (though sorting requires materialization).
    """
    return SortTable(table, field)
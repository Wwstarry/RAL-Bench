"""
Core table implementation and basic functions.
"""

class Table:
    """Lazy table wrapper that chains transformations."""
    
    def __init__(self, source):
        self.source = source
    
    def __iter__(self):
        """Iterate over rows, materializing the data."""
        return iter(self.source)
    
    def convert(self, field, func):
        """Apply a conversion function to a field."""
        from .transform.conversions import convert
        return convert(self, field, func)
    
    def addfield(self, fieldname, func):
        """Add a new field computed from existing fields."""
        from .transform.conversions import addfield
        return addfield(self, fieldname, func)
    
    def select(self, predicate):
        """Filter rows using a predicate function."""
        from .transform.selects import select
        return select(self, predicate)
    
    def selectge(self, field, threshold):
        """Select rows where field >= threshold."""
        from .transform.selects import selectge
        return selectge(self, field, threshold)
    
    def selectgt(self, field, threshold):
        """Select rows where field > threshold."""
        from .transform.selects import selectgt
        return selectgt(self, field, threshold)
    
    def sort(self, field):
        """Sort table by field."""
        from .transform.sort import sort
        return sort(self, field)
    
    def join(self, right, key='id'):
        """Join with another table on key field."""
        from .transform.joins import join
        return join(self, right, key)
    
    def tocsv(self, path):
        """Write table to CSV file."""
        from .io.csv import tocsv
        return tocsv(self, path)


def fromdicts(records, header=None):
    """Create table from list of dictionaries."""
    if not records:
        return Table(iter([[]]))
    
    if header is None:
        # Extract header from first record keys
        header = list(records[0].keys())
    
    def _generate_rows():
        yield header
        for record in records:
            row = [record.get(field) for field in header]
            yield row
    
    return Table(_generate_rows())
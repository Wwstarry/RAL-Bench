"""
Sorting operations.
"""

from petl.table import Table


class SortTable(Table):
    """Table that sorts rows by a field."""
    
    def __init__(self, source, field, reverse=False):
        self.source = source
        self.field = field
        self.reverse = reverse
    
    def __iter__(self):
        source_iter = iter(self.source)
        header = next(source_iter)
        
        try:
            field_index = header.index(self.field)
        except ValueError:
            raise ValueError(f"Field '{self.field}' not found in header")
        
        # Collect all rows
        rows = list(source_iter)
        
        # Sort rows by field value
        try:
            rows.sort(key=lambda row: row[field_index], reverse=self.reverse)
        except TypeError:
            # Handle mixed types by converting to string for comparison
            rows.sort(
                key=lambda row: (row[field_index] is None, str(row[field_index])),
                reverse=self.reverse
            )
        
        yield header
        for row in rows:
            yield row


def sort(table, field, reverse=False):
    """
    Sort a table by a field.
    
    Args:
        table: A Table object
        field: The field name to sort by
        reverse: If True, sort in descending order
    
    Returns:
        A new Table object
    """
    return SortTable(table, field, reverse=reverse)
"""
Column conversion operations.
"""

from petl.table import Table


class ConvertTable(Table):
    """Table that applies a conversion function to a field."""
    
    def __init__(self, source, field, func):
        self.source = source
        self.field = field
        self.func = func
    
    def __iter__(self):
        source_iter = iter(self.source)
        header = next(source_iter)
        
        # Find the index of the field
        try:
            field_index = header.index(self.field)
        except ValueError:
            raise ValueError(f"Field '{self.field}' not found in header")
        
        yield header
        
        # Apply conversion to each row
        for row in source_iter:
            row = list(row)
            try:
                row[field_index] = self.func(row[field_index])
            except Exception:
                # If conversion fails, leave the value as is
                pass
            yield row


def convert(table, field, func):
    """
    Apply a conversion function to a field in a table.
    
    Args:
        table: A Table object
        field: The field name to convert
        func: A function that takes a value and returns a converted value
    
    Returns:
        A new Table object
    """
    return ConvertTable(table, field, func)
"""
Field creation and manipulation operations.
"""

from petl.table import Table


class AddFieldTable(Table):
    """Table that adds a new field computed from a function."""
    
    def __init__(self, source, fieldname, func):
        self.source = source
        self.fieldname = fieldname
        self.func = func
    
    def __iter__(self):
        source_iter = iter(self.source)
        header = next(source_iter)
        
        # Add new field to header
        new_header = list(header) + [self.fieldname]
        yield new_header
        
        # Compute new field for each row
        for row in source_iter:
            row = list(row)
            try:
                new_value = self.func(row)
            except Exception:
                new_value = None
            row.append(new_value)
            yield row


def addfield(table, fieldname, func):
    """
    Add a new field to a table computed from a function.
    
    Args:
        table: A Table object
        fieldname: The name of the new field
        func: A function that takes a row and returns a value
    
    Returns:
        A new Table object
    """
    return AddFieldTable(table, fieldname, func)
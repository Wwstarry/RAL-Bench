"""
Field conversion operations.
"""

def convert(table, field, func):
    """Apply conversion function to specified field."""
    def _convert_rows():
        it = iter(table)
        header = next(it)
        
        if field not in header:
            raise ValueError(f"Field '{field}' not found in header: {header}")
        
        field_index = header.index(field)
        yield header
        
        for row in it:
            if len(row) > field_index:
                new_row = list(row)
                new_row[field_index] = func(row[field_index])
                yield new_row
            else:
                yield row
    
    from ..core import Table
    return Table(_convert_rows())


def addfield(table, fieldname, func):
    """Add a new field computed from existing fields."""
    def _addfield_rows():
        it = iter(table)
        header = next(it)
        
        if fieldname in header:
            raise ValueError(f"Field '{fieldname}' already exists in header")
        
        new_header = header + [fieldname]
        yield new_header
        
        for row in it:
            # Pass the row as a list to the function
            new_value = func(row)
            new_row = row + [new_value]
            yield new_row
    
    from ..core import Table
    return Table(_addfield_rows())
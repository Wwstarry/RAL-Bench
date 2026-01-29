"""
Conversion and field manipulation operations.
"""


class ConvertTable:
    """Lazy table that applies a conversion function to a field."""
    
    def __init__(self, source, field, func):
        self.source = source
        self.field = field
        self.func = func
    
    def __iter__(self):
        it = iter(self.source)
        header = next(it)
        yield header
        
        # Find the index of the field to convert
        try:
            field_idx = header.index(self.field)
        except ValueError:
            raise ValueError(f"Field '{self.field}' not found in header")
        
        # Apply conversion to each row
        for row in it:
            row_list = list(row)
            row_list[field_idx] = self.func(row_list[field_idx])
            yield tuple(row_list)


class AddFieldTable:
    """Lazy table that adds a new field."""
    
    def __init__(self, source, fieldname, func):
        self.source = source
        self.fieldname = fieldname
        self.func = func
    
    def __iter__(self):
        it = iter(self.source)
        header = next(it)
        
        # Add new field to header
        new_header = tuple(list(header) + [self.fieldname])
        yield new_header
        
        # Add computed value to each row
        for row in it:
            # Pass the row as a dict-like object to the function
            row_dict = dict(zip(header, row))
            new_value = self.func(row_dict)
            new_row = tuple(list(row) + [new_value])
            yield new_row


class DictsTable:
    """Lazy table constructed from a list of dictionaries."""
    
    def __init__(self, records, header=None):
        self.records = records
        self.header = header
    
    def __iter__(self):
        if not self.records:
            if self.header:
                yield tuple(self.header)
            return
        
        # Determine header
        if self.header:
            header = tuple(self.header)
        else:
            # Use keys from first record
            header = tuple(self.records[0].keys())
        
        yield header
        
        # Yield data rows
        for record in self.records:
            row = tuple(record.get(field, None) for field in header)
            yield row


def convert(table, field, func):
    """
    Apply a conversion function to a field.
    
    Returns a lazy table wrapper.
    """
    return ConvertTable(table, field, func)


def addfield(table, fieldname, func):
    """
    Add a new field computed from existing fields.
    
    The func receives a dict-like object representing the row.
    Returns a lazy table wrapper.
    """
    return AddFieldTable(table, fieldname, func)


def fromdicts(records, header=None):
    """
    Construct a table from a list of dictionaries.
    
    Returns a lazy table wrapper.
    """
    return DictsTable(records, header)
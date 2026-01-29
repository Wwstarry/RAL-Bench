"""
Row selection and filtering operations.
"""


class SelectTable:
    """Lazy table that filters rows based on a predicate."""
    
    def __init__(self, source, predicate):
        self.source = source
        self.predicate = predicate
    
    def __iter__(self):
        it = iter(self.source)
        header = next(it)
        yield header
        
        # Filter rows based on predicate
        for row in it:
            row_dict = dict(zip(header, row))
            if self.predicate(row_dict):
                yield row


class SelectCompareTable:
    """Lazy table that filters rows based on field comparison."""
    
    def __init__(self, source, field, threshold, op):
        self.source = source
        self.field = field
        self.threshold = threshold
        self.op = op
    
    def __iter__(self):
        it = iter(self.source)
        header = next(it)
        yield header
        
        # Find the index of the field
        try:
            field_idx = header.index(self.field)
        except ValueError:
            raise ValueError(f"Field '{self.field}' not found in header")
        
        # Filter rows based on comparison
        for row in it:
            value = row[field_idx]
            if self.op(value, self.threshold):
                yield row


def select(table, predicate):
    """
    Select rows where predicate returns True.
    
    The predicate receives a dict-like object representing the row.
    Returns a lazy table wrapper.
    """
    return SelectTable(table, predicate)


def selectge(table, field, threshold):
    """
    Select rows where field >= threshold.
    
    Returns a lazy table wrapper.
    """
    return SelectCompareTable(table, field, threshold, lambda a, b: a >= b)


def selectgt(table, field, threshold):
    """
    Select rows where field > threshold.
    
    Returns a lazy table wrapper.
    """
    return SelectCompareTable(table, field, threshold, lambda a, b: a > b)
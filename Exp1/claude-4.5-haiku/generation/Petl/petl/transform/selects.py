"""
Row filtering operations.
"""

from petl.table import Table


class SelectTable(Table):
    """Table that filters rows based on a predicate."""
    
    def __init__(self, source, predicate):
        self.source = source
        self.predicate = predicate
    
    def __iter__(self):
        source_iter = iter(self.source)
        header = next(source_iter)
        yield header
        
        # Filter rows based on predicate
        for row in source_iter:
            if self.predicate(row):
                yield row


class SelectGeTable(Table):
    """Table that filters rows where a field is >= a threshold."""
    
    def __init__(self, source, field, threshold):
        self.source = source
        self.field = field
        self.threshold = threshold
    
    def __iter__(self):
        source_iter = iter(self.source)
        header = next(source_iter)
        
        try:
            field_index = header.index(self.field)
        except ValueError:
            raise ValueError(f"Field '{self.field}' not found in header")
        
        yield header
        
        for row in source_iter:
            try:
                value = row[field_index]
                if value is not None and value >= self.threshold:
                    yield row
            except (TypeError, IndexError):
                pass


class SelectGtTable(Table):
    """Table that filters rows where a field is > a threshold."""
    
    def __init__(self, source, field, threshold):
        self.source = source
        self.field = field
        self.threshold = threshold
    
    def __iter__(self):
        source_iter = iter(self.source)
        header = next(source_iter)
        
        try:
            field_index = header.index(self.field)
        except ValueError:
            raise ValueError(f"Field '{self.field}' not found in header")
        
        yield header
        
        for row in source_iter:
            try:
                value = row[field_index]
                if value is not None and value > self.threshold:
                    yield row
            except (TypeError, IndexError):
                pass


def select(table, predicate):
    """
    Filter rows in a table based on a predicate function.
    
    Args:
        table: A Table object
        predicate: A function that takes a row and returns True/False
    
    Returns:
        A new Table object
    """
    return SelectTable(table, predicate)


def selectge(table, field, threshold):
    """
    Filter rows where a field value is >= threshold.
    
    Args:
        table: A Table object
        field: The field name to compare
        threshold: The threshold value
    
    Returns:
        A new Table object
    """
    return SelectGeTable(table, field, threshold)


def selectgt(table, field, threshold):
    """
    Filter rows where a field value is > threshold.
    
    Args:
        table: A Table object
        field: The field name to compare
        threshold: The threshold value
    
    Returns:
        A new Table object
    """
    return SelectGtTable(table, field, threshold)
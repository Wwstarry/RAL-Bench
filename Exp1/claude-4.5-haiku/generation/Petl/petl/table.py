"""
Core table abstraction and utilities.
"""


class Table:
    """Base class for lazy table wrappers."""
    
    def __iter__(self):
        """Iterate over rows (header first, then data rows)."""
        raise NotImplementedError
    
    def __repr__(self):
        return f"<{self.__class__.__name__}>"


class DictTable(Table):
    """Table constructed from a list of dictionaries."""
    
    def __init__(self, records, header=None):
        self.records = records
        self._header = header
    
    def __iter__(self):
        if not self.records:
            if self._header:
                yield self._header
            return
        
        # Determine header from first record if not provided
        if self._header:
            header = self._header
        else:
            header = list(self.records[0].keys())
        
        yield header
        
        # Yield data rows
        for record in self.records:
            row = [record.get(field) for field in header]
            yield row


def fromdicts(records, header=None):
    """
    Create a table from a list of dictionaries.
    
    Args:
        records: List of dictionaries
        header: Optional list of field names (column order)
    
    Returns:
        A Table object
    """
    return DictTable(records, header=header)
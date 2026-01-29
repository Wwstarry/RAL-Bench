"""
Row selection and filtering operations.
"""

def select(table, predicate):
    """Filter rows using a predicate function."""
    def _select_rows():
        it = iter(table)
        header = next(it)
        yield header
        
        for row in it:
            if predicate(row):
                yield row
    
    from ..core import Table
    return Table(_select_rows())


def selectge(table, field, threshold):
    """Select rows where field >= threshold."""
    def _selectge_rows():
        it = iter(table)
        header = next(it)
        
        if field not in header:
            raise ValueError(f"Field '{field}' not found in header: {header}")
        
        field_index = header.index(field)
        yield header
        
        for row in it:
            if len(row) > field_index and row[field_index] is not None:
                try:
                    if float(row[field_index]) >= threshold:
                        yield row
                except (ValueError, TypeError):
                    # Handle non-numeric values
                    if row[field_index] >= threshold:
                        yield row
            else:
                # Skip rows with missing field
                pass
    
    from ..core import Table
    return Table(_selectge_rows())


def selectgt(table, field, threshold):
    """Select rows where field > threshold."""
    def _selectgt_rows():
        it = iter(table)
        header = next(it)
        
        if field not in header:
            raise ValueError(f"Field '{field}' not found in header: {header}")
        
        field_index = header.index(field)
        yield header
        
        for row in it:
            if len(row) > field_index and row[field_index] is not None:
                try:
                    if float(row[field_index]) > threshold:
                        yield row
                except (ValueError, TypeError):
                    # Handle non-numeric values
                    if row[field_index] > threshold:
                        yield row
            else:
                # Skip rows with missing field
                pass
    
    from ..core import Table
    return Table(_selectgt_rows())
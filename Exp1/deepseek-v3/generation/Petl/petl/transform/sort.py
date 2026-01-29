"""
Sorting operations.
"""

def sort(table, field):
    """Sort table by specified field."""
    def _sort_rows():
        it = iter(table)
        header = next(it)
        
        if field not in header:
            raise ValueError(f"Field '{field}' not found in header: {header}")
        
        field_index = header.index(field)
        yield header
        
        # Materialize and sort the data rows
        rows = list(it)
        rows.sort(key=lambda row: row[field_index] if len(row) > field_index else None)
        
        for row in rows:
            yield row
    
    from ..core import Table
    return Table(_sort_rows())
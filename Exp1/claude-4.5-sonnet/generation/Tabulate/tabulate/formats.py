"""
Table format definitions and utilities
"""

from tabulate.core import TableFormat, Line, DataRow, simple_separated_format


# Export common formats
def get_format(name):
    """Get a table format by name"""
    from tabulate.core import _table_formats
    return _table_formats.get(name)


def list_formats():
    """List all available table format names"""
    from tabulate.core import _table_formats
    return list(_table_formats.keys())


__all__ = ["TableFormat", "Line", "DataRow", "simple_separated_format",
           "get_format", "list_formats"]
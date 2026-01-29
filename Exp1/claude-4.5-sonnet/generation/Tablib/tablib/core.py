"""Core tabular data structures."""

import copy
from typing import Any, List, Optional, Tuple, Union, Iterable


class Dataset:
    """A tabular dataset with headers and rows."""
    
    def __init__(self, *args, headers=None):
        """Initialize a Dataset.
        
        Args:
            *args: Variable number of row tuples/lists
            headers: Optional iterable of column names
        """
        self._data = []
        self._headers = None
        self.title = None
        
        # Set headers first if provided
        if headers is not None:
            self.headers = headers
        
        # Add rows
        for row in args:
            self.append(row)
    
    @property
    def headers(self):
        """Get the column headers."""
        return self._headers
    
    @headers.setter
    def headers(self, value):
        """Set the column headers."""
        if value is None:
            self._headers = None
        else:
            self._headers = list(value)
    
    @property
    def height(self):
        """Number of rows in the dataset."""
        return len(self._data)
    
    @property
    def width(self):
        """Number of columns in the dataset."""
        if self._headers:
            return len(self._headers)
        elif self._data:
            return len(self._data[0])
        return 0
    
    def append(self, row):
        """Append a row to the dataset.
        
        Args:
            row: An iterable of values
        """
        self._data.append(tuple(row))
    
    def append_col(self, values, header=None):
        """Append a column to the dataset.
        
        Args:
            values: An iterable of values (must match current height)
            header: Optional column name
        """
        values_list = list(values)
        
        # If dataset is empty, initialize with empty rows
        if not self._data:
            for val in values_list:
                self._data.append((val,))
        else:
            # Ensure values match height
            if len(values_list) != self.height:
                raise ValueError(f"Column values length {len(values_list)} does not match dataset height {self.height}")
            
            # Append to each row
            new_data = []
            for i, row in enumerate(self._data):
                new_row = list(row)
                new_row.append(values_list[i])
                new_data.append(tuple(new_row))
            self._data = new_data
        
        # Add header if provided
        if header is not None:
            if self._headers is None:
                # Initialize headers with empty strings for existing columns
                self._headers = [''] * (self.width - 1)
            self._headers.append(header)
    
    def __getitem__(self, key):
        """Get rows by slice or column by name.
        
        Args:
            key: Either a slice for rows or a string for column access
            
        Returns:
            For slice: list of row tuples
            For string: list of column values
        """
        if isinstance(key, slice):
            return self._data[key]
        elif isinstance(key, str):
            # Column access by header name
            if self._headers is None:
                raise KeyError(f"No headers defined")
            if key not in self._headers:
                raise KeyError(f"Column '{key}' not found")
            
            col_index = self._headers.index(key)
            return [row[col_index] if col_index < len(row) else None for row in self._data]
        else:
            raise TypeError(f"Invalid key type: {type(key)}")
    
    @property
    def dict(self):
        """Return dataset as a list of dictionaries.
        
        Returns:
            List of dicts mapping headers to values
        """
        if self._headers is None:
            return []
        
        result = []
        for row in self._data:
            row_dict = {}
            for i, header in enumerate(self._headers):
                row_dict[header] = row[i] if i < len(row) else None
            result.append(row_dict)
        return result
    
    def export(self, fmt):
        """Export dataset to a format.
        
        Args:
            fmt: Format string ('csv', 'json', etc.)
            
        Returns:
            String representation in the requested format
        """
        fmt = fmt.lower()
        
        if fmt == 'csv':
            from tablib.formats import _csv
            return _csv.export_set(self)
        elif fmt == 'json':
            from tablib.formats import _json
            return _json.export_set(self)
        else:
            raise ValueError(f"Unsupported format: {fmt}")
    
    @property
    def csv(self):
        """Export to CSV format."""
        return self.export('csv')
    
    @csv.setter
    def csv(self, value):
        """Import from CSV format."""
        from tablib.formats import _csv
        _csv.import_set(self, value)
    
    @property
    def json(self):
        """Export to JSON format."""
        return self.export('json')
    
    @json.setter
    def json(self, value):
        """Import from JSON format."""
        from tablib.formats import _json
        _json.import_set(self, value)


class Databook:
    """A collection of datasets (sheets)."""
    
    def __init__(self, datasets=None):
        """Initialize a Databook.
        
        Args:
            datasets: Optional iterable of Dataset instances
        """
        self._datasets = []
        if datasets:
            self._datasets = list(datasets)
    
    @property
    def size(self):
        """Number of datasets in the book."""
        return len(self._datasets)
    
    def sheets(self):
        """Return an iterable of datasets.
        
        Returns:
            List of Dataset instances
        """
        return self._datasets
    
    def __iter__(self):
        """Iterate over datasets."""
        return iter(self._datasets)
    
    def export(self, fmt):
        """Export databook to a format.
        
        Args:
            fmt: Format string ('json', etc.)
            
        Returns:
            String representation in the requested format
        """
        fmt = fmt.lower()
        
        if fmt == 'json':
            from tablib.formats import _json
            return _json.export_book(self)
        else:
            raise ValueError(f"Unsupported format: {fmt}")
    
    @property
    def json(self):
        """Export to JSON format."""
        return self.export('json')
    
    @json.setter
    def json(self, value):
        """Import from JSON format."""
        from tablib.formats import _json
        _json.import_book(self, value)
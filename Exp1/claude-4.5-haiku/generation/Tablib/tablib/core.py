"""
Core tablib module providing Dataset and Databook classes.
"""

import json as json_module
from io import StringIO
from tablib.formats import _csv, _json


class Dataset:
    """
    A tabular data container supporting rows, columns, and multiple export formats.
    """

    def __init__(self, *rows, headers=None):
        """
        Initialize a Dataset.

        Args:
            *rows: Variable number of row iterables.
            headers: Optional iterable of column header names.
        """
        self._data = []
        self._headers = list(headers) if headers else []
        self.title = None

        for row in rows:
            self.append(row)

    def append(self, row):
        """
        Append a single row to the dataset.

        Args:
            row: An iterable of field values.
        """
        row_tuple = tuple(row)
        if self._headers and len(row_tuple) != len(self._headers):
            raise ValueError(
                f"Row length {len(row_tuple)} does not match header length {len(self._headers)}"
            )
        self._data.append(row_tuple)

    def append_col(self, values, header=None):
        """
        Append a new column to the dataset.

        Args:
            values: An iterable of values for the new column.
            header: Optional header name for the new column.
        """
        values_list = list(values)
        if len(values_list) != len(self._data):
            raise ValueError(
                f"Column length {len(values_list)} does not match dataset height {len(self._data)}"
            )

        # Add header if provided
        if header is not None:
            self._headers.append(header)
        else:
            self._headers.append(None)

        # Append value to each row
        for i, value in enumerate(values_list):
            self._data[i] = self._data[i] + (value,)

    @property
    def headers(self):
        """Get the column headers."""
        return self._headers

    @headers.setter
    def headers(self, value):
        """Set the column headers."""
        self._headers = list(value) if value else []

    @property
    def height(self):
        """Get the number of rows."""
        return len(self._data)

    @property
    def width(self):
        """Get the number of columns."""
        return len(self._headers) if self._headers else (len(self._data[0]) if self._data else 0)

    def __getitem__(self, key):
        """
        Support indexing and slicing.

        Args:
            key: An integer index, slice, or column name string.

        Returns:
            A row tuple for integer index, a list of row tuples for slice,
            or a list of column values for string key.
        """
        if isinstance(key, str):
            # Column access by name
            if key not in self._headers:
                raise KeyError(f"Column '{key}' not found")
            col_index = self._headers.index(key)
            return [row[col_index] for row in self._data]
        elif isinstance(key, slice):
            # Slice access
            return self._data[key]
        else:
            # Integer index access
            return self._data[key]

    @property
    def dict(self):
        """
        Get a list of dictionaries, one per row.

        Returns:
            A list of dictionaries mapping header names to cell values.
        """
        result = []
        for row in self._data:
            row_dict = {}
            for i, header in enumerate(self._headers):
                row_dict[header] = row[i]
            result.append(row_dict)
        return result

    def export(self, fmt):
        """
        Export the dataset to a specified format.

        Args:
            fmt: The format string ('csv' or 'json').

        Returns:
            A string representation of the dataset in the specified format.
        """
        if fmt == "csv":
            return _csv.export_csv(self)
        elif fmt == "json":
            return _json.export_json(self)
        else:
            raise ValueError(f"Unsupported format: {fmt}")

    @property
    def csv(self):
        """Get the dataset as a CSV string."""
        return self.export("csv")

    @csv.setter
    def csv(self, value):
        """Set the dataset from a CSV string."""
        dataset = _csv.import_csv(value)
        self._data = dataset._data
        self._headers = dataset._headers

    @property
    def json(self):
        """Get the dataset as a JSON string."""
        return self.export("json")

    @json.setter
    def json(self, value):
        """Set the dataset from a JSON string."""
        dataset = _json.import_json(value)
        self._data = dataset._data
        self._headers = dataset._headers


class Databook:
    """
    A container for multiple Dataset objects (sheets).
    """

    def __init__(self, datasets):
        """
        Initialize a Databook.

        Args:
            datasets: An iterable of Dataset instances.
        """
        self._sheets = list(datasets)

    @property
    def size(self):
        """Get the number of sheets in the book."""
        return len(self._sheets)

    def sheets(self):
        """
        Get the sheets in the book.

        Returns:
            An iterable of Dataset objects.
        """
        return iter(self._sheets)

    def __iter__(self):
        """Iterate over the sheets in the book."""
        return iter(self._sheets)

    def export(self, fmt):
        """
        Export the databook to a specified format.

        Args:
            fmt: The format string ('json').

        Returns:
            A string representation of the databook in the specified format.
        """
        if fmt == "json":
            return _json.export_databook_json(self)
        else:
            raise ValueError(f"Unsupported format for Databook: {fmt}")

    @property
    def json(self):
        """Get the databook as a JSON string."""
        return self.export("json")

    @json.setter
    def json(self, value):
        """Set the databook from a JSON string."""
        databook = _json.import_databook_json(value)
        self._sheets = databook._sheets
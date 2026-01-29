# -*- coding: utf-8 -*-

class Dataset:
    """A container for tabular data."""

    def __init__(self, *rows, headers=None, title=None):
        self._headers = list(headers) if headers is not None else []
        self._data = [list(row) for row in rows]
        self.title = title

        if self._headers and self._data:
            if any(len(row) != len(self._headers) for row in self._data):
                raise ValueError("Row length must match header length.")

    @property
    def headers(self):
        return self._headers

    @headers.setter
    def headers(self, headers):
        headers = list(headers)
        if self.width and len(headers) != self.width:
            raise ValueError(
                f"Invalid headers length. Expected {self.width}, got {len(headers)}"
            )
        self._headers = headers

    @property
    def height(self):
        return len(self._data)

    @property
    def width(self):
        if self._headers:
            return len(self._headers)
        if self._data:
            return len(self._data[0])
        return 0

    def wipe(self):
        """Removes all data and headers."""
        self._headers = []
        self._data = []

    def append(self, row):
        """Adds a row to the dataset."""
        row = list(row)
        if self.width > 0 and len(row) != self.width:
            raise ValueError(
                f"Appended row length {len(row)} does not match dataset width {self.width}"
            )
        self._data.append(row)

    def append_col(self, col, header=None):
        """Adds a column to the dataset."""
        col = list(col)
        if self.height > 0 and len(col) != self.height:
            raise ValueError(
                f"Appended column length {len(col)} does not match dataset height {self.height}"
            )

        self._headers.append(header)

        if not self._data:
            self._data = [[c] for c in col]
        else:
            for i, row in enumerate(self._data):
                row.append(col[i])

    def __getitem__(self, key):
        if isinstance(key, str):
            try:
                i = self._headers.index(key)
                return [r[i] for r in self._data]
            except ValueError:
                raise KeyError(f"Column '{key}' not found in headers")
        elif isinstance(key, slice):
            return [tuple(r) for r in self._data[key]]
        elif isinstance(key, int):
            return tuple(self._data[key])
        else:
            raise TypeError("Dataset indices must be integers, slices, or strings")

    def __iter__(self):
        return (tuple(row) for row in self._data)

    def __repr__(self):
        return f"<Dataset headers={self.headers!r} rows={self.height}>"

    @property
    def dict(self):
        """Returns a list of dictionaries, one per row."""
        if not self.headers:
            return []
        return [dict(zip(self.headers, row)) for row in self._data]

    def export(self, fmt):
        """Exports the dataset to a given format."""
        if fmt not in _formats:
            raise NotImplementedError(f"Format '{fmt}' is not supported.")
        return _formats[fmt].export_set(self)

    @property
    def csv(self):
        return self.export('csv')

    @csv.setter
    def csv(self, value):
        _formats['csv'].import_set(self, value)

    @property
    def json(self):
        return self.export('json')

    @json.setter
    def json(self, value):
        _formats['json'].import_set(self, value)


class Databook:
    """A container for multiple Datasets."""

    def __init__(self, datasets=None):
        self._datasets = []
        if datasets:
            for d in datasets:
                self.add_sheet(d)

    @property
    def size(self):
        return len(self._datasets)

    def wipe(self):
        """Removes all datasets from the book."""
        self._datasets = []

    def add_sheet(self, dataset):
        """Adds a Dataset to the book."""
        if not isinstance(dataset, Dataset):
            raise TypeError("Only Dataset objects can be added to a Databook.")
        self._datasets.append(dataset)

    def sheets(self):
        """Returns a list of all datasets in the book."""
        return self._datasets

    def __iter__(self):
        return iter(self.sheets())

    def __repr__(self):
        return f"<Databook sheets={self.size}>"

    def export(self, fmt):
        """Exports the databook to a given format."""
        if fmt not in _formats:
            raise NotImplementedError(f"Format '{fmt}' is not supported.")
        if not hasattr(_formats[fmt], 'export_book'):
            raise NotImplementedError(f"Format '{fmt}' does not support Databooks.")
        return _formats[fmt].export_book(self)

    @property
    def json(self):
        return self.export('json')

    @json.setter
    def json(self, value):
        _formats['json'].import_book(self, value)

# --- Format Registry ---
_formats = {}

def register_format(name, module):
    _formats[name] = module

# Import and register formats
from .formats import _csv, _json

register_format('csv', _csv)
register_format('json', _json)
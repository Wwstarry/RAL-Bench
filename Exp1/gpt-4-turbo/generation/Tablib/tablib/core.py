import copy

from .formats import _csv, _json

class Dataset:
    def __init__(self, *rows, headers=None):
        self._headers = list(headers) if headers is not None else None
        self._data = []
        for row in rows:
            self.append(row)
        self.title = None

    @property
    def headers(self):
        return self._headers

    @headers.setter
    def headers(self, value):
        if value is None:
            self._headers = None
        else:
            self._headers = list(value)

    @property
    def height(self):
        return len(self._data)

    @property
    def width(self):
        if self._headers is not None:
            return len(self._headers)
        elif self.height > 0:
            return len(self._data[0])
        else:
            return 0

    def __getitem__(self, key):
        if isinstance(key, slice):
            # Return a list of row tuples
            return [tuple(row) for row in self._data[key]]
        elif isinstance(key, str):
            # Column access by header name
            idx = self._get_col_index(key)
            return [row[idx] if idx < len(row) else None for row in self._data]
        else:
            # Single row access
            return tuple(self._data[key])

    def _get_col_index(self, col_name):
        if self._headers is None:
            raise KeyError("No headers defined")
        try:
            return self._headers.index(col_name)
        except ValueError:
            raise KeyError(col_name)

    def append(self, row):
        row = list(row)
        if self._headers is not None:
            if len(row) != len(self._headers):
                raise ValueError("Row length does not match headers")
        elif self.height > 0:
            if len(row) != len(self._data[0]):
                raise ValueError("Row length does not match existing rows")
        self._data.append(row)

    def append_col(self, values, header=None):
        values = list(values)
        if len(values) != self.height:
            raise ValueError("Column length does not match dataset height")
        for i, value in enumerate(values):
            if i < self.height:
                self._data[i].append(value)
        if self._headers is not None:
            if header is None:
                self._headers.append('')
            else:
                self._headers.append(header)
        elif self.height > 0:
            if header is not None:
                self._headers = [''] * (self.width - 1) + [header]

    def export(self, fmt):
        fmt = fmt.lower()
        if fmt == 'csv':
            return _csv.export_set(self)
        elif fmt == 'json':
            return _json.export_set(self)
        else:
            raise ValueError("Unknown format: %r" % fmt)

    @property
    def csv(self):
        return _csv.export_set(self)

    @csv.setter
    def csv(self, value):
        ds = _csv.import_set(value)
        self._headers = ds.headers
        self._data = ds._data

    @property
    def json(self):
        return _json.export_set(self)

    @json.setter
    def json(self, value):
        ds = _json.import_set(value)
        self._headers = ds.headers
        self._data = ds._data

    @property
    def dict(self):
        if self._headers is None:
            return [list(row) for row in self._data]
        result = []
        for row in self._data:
            d = {}
            for i, h in enumerate(self._headers):
                d[h] = row[i] if i < len(row) else None
            result.append(d)
        return result

    def __len__(self):
        return self.height

    def __iter__(self):
        for row in self._data:
            yield tuple(row)

class Databook:
    def __init__(self, datasets):
        self._datasets = []
        for ds in datasets:
            self._datasets.append(ds)
        self.size = len(self._datasets)

    def sheets(self):
        return self._datasets

    def __iter__(self):
        return iter(self._datasets)

    def export(self, fmt):
        fmt = fmt.lower()
        if fmt == 'json':
            return _json.export_book(self)
        else:
            raise ValueError("Unknown format: %r" % fmt)

    @property
    def json(self):
        return _json.export_book(self)

    @json.setter
    def json(self, value):
        book = _json.import_book(value)
        self._datasets = book._datasets
        self.size = len(self._datasets)
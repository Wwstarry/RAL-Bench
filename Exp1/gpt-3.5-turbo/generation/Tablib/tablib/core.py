import io
from collections.abc import Iterable

from .formats import _csv, _json


class Dataset:
    def __init__(self, *rows, headers=None):
        # headers: iterable or None
        # rows: each row is iterable of values
        if headers is not None:
            self._headers = list(headers)
        else:
            self._headers = []

        self._data = []
        for row in rows:
            self.append(row)

        # title attribute for Databook sheets
        self.title = None

    @property
    def headers(self):
        return self._headers

    @headers.setter
    def headers(self, value):
        if value is None:
            self._headers = []
        else:
            self._headers = list(value)

    @property
    def height(self):
        return len(self._data)

    @property
    def width(self):
        return len(self._headers)

    def __getitem__(self, key):
        # Support slicing rows: dataset[start:stop]
        if isinstance(key, slice):
            # Return list of tuples for rows in slice
            return [tuple(row) for row in self._data[key]]
        # Support dict-style column access: dataset['column_name']
        elif isinstance(key, str):
            if key not in self._headers:
                raise KeyError(f"Column '{key}' not found")
            idx = self._headers.index(key)
            return (row[idx] for row in self._data)
        else:
            raise TypeError("Invalid key type. Use slice or column name string.")

    def append(self, row):
        # row: iterable of values
        row = list(row)
        if self.width == 0 and self._headers:
            # headers exist but no columns yet, so width = len(headers)
            expected_width = len(self._headers)
        else:
            expected_width = self.width

        if expected_width == 0:
            # no headers and no columns yet, infer width from row
            expected_width = len(row)
            if not self._headers:
                self._headers = [None] * expected_width

        if len(row) != expected_width:
            raise ValueError(f"Row length {len(row)} does not match dataset width {expected_width}")

        self._data.append(row)

    def append_col(self, values, header=None):
        # values: iterable of length == height
        values = list(values)
        if self.height == 0:
            # no rows yet, create rows with one column each
            for v in values:
                self._data.append([v])
            if header is None:
                header = None
            self._headers.append(header)
        else:
            if len(values) != self.height:
                raise ValueError(f"Column length {len(values)} does not match dataset height {self.height}")
            for i, v in enumerate(values):
                self._data[i].append(v)
            self._headers.append(header)

    def export(self, fmt):
        fmt = fmt.lower()
        if fmt == 'csv':
            return self.csv
        elif fmt == 'json':
            return self.json
        else:
            raise ValueError(f"Unsupported export format: {fmt}")

    @property
    def csv(self):
        return _csv.export_set(self)

    @csv.setter
    def csv(self, csv_string):
        ds = _csv.import_set(csv_string)
        self._headers = ds._headers
        self._data = ds._data

    @property
    def json(self):
        return _json.export_set(self)

    @json.setter
    def json(self, json_string):
        ds = _json.import_set(json_string)
        self._headers = ds._headers
        self._data = ds._data

    @property
    def dict(self):
        # list of dicts, one per row, mapping header to value
        result = []
        for row in self._data:
            d = {}
            for i, h in enumerate(self._headers):
                d[h] = row[i]
            result.append(d)
        return result


class Databook:
    def __init__(self, datasets):
        # datasets: iterable of Dataset instances
        self._sheets = list(datasets)

    @property
    def size(self):
        return len(self._sheets)

    def sheets(self):
        return iter(self._sheets)

    def __iter__(self):
        return iter(self._sheets)

    def export(self, fmt):
        fmt = fmt.lower()
        if fmt == 'json':
            return self.json
        else:
            raise ValueError(f"Unsupported export format: {fmt}")

    @property
    def json(self):
        return _json.export_book(self)

    @json.setter
    def json(self, json_string):
        book = _json.import_book(json_string)
        self._sheets = book._sheets
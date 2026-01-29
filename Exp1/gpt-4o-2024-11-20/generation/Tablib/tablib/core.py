import csv
import json
from collections import OrderedDict

class Dataset:
    def __init__(self, *rows, headers=None):
        self._headers = list(headers) if headers else []
        self._data = [list(row) for row in rows]
        self._validate()

    def _validate(self):
        if self._data and self._headers and len(self._headers) != len(self._data[0]):
            raise ValueError("Number of headers must match the number of columns in rows")

    @property
    def headers(self):
        return self._headers

    @headers.setter
    def headers(self, headers):
        if headers and len(headers) != self.width:
            raise ValueError("Number of headers must match the number of columns")
        self._headers = list(headers)

    @property
    def height(self):
        return len(self._data)

    @property
    def width(self):
        return len(self._headers) if self._headers else (len(self._data[0]) if self._data else 0)

    def __getitem__(self, key):
        if isinstance(key, slice):
            return [tuple(row) for row in self._data[key]]
        elif isinstance(key, str):
            if key not in self._headers:
                raise KeyError(f"Column '{key}' not found in headers")
            idx = self._headers.index(key)
            return [row[idx] for row in self._data]
        else:
            raise TypeError("Invalid key type")

    def append(self, row):
        if len(row) != self.width:
            raise ValueError("Row length must match the number of columns")
        self._data.append(list(row))

    def append_col(self, values, header=None):
        if len(values) != self.height:
            raise ValueError("Column length must match the number of rows")
        for i, value in enumerate(values):
            self._data[i].append(value)
        if header:
            self._headers.append(header)

    def export(self, fmt):
        if fmt == 'csv':
            from .formats._csv import export_set
            return export_set(self)
        elif fmt == 'json':
            from .formats._json import export_set
            return export_set(self)
        else:
            raise ValueError(f"Unsupported format: {fmt}")

    @property
    def csv(self):
        return self.export('csv')

    @csv.setter
    def csv(self, csv_string):
        from .formats._csv import import_set
        imported = import_set(csv_string)
        self._headers = imported.headers
        self._data = imported._data

    @property
    def json(self):
        return self.export('json')

    @json.setter
    def json(self, json_string):
        from .formats._json import import_set
        imported = import_set(json_string)
        self._headers = imported.headers
        self._data = imported._data

    @property
    def dict(self):
        return [OrderedDict(zip(self._headers, row)) for row in self._data]


class Databook:
    def __init__(self, datasets):
        self._datasets = list(datasets)

    @property
    def size(self):
        return len(self._datasets)

    def sheets(self):
        return iter(self._datasets)

    def __iter__(self):
        return self.sheets()

    def export(self, fmt):
        if fmt == 'json':
            from .formats._json import export_book
            return export_book(self)
        else:
            raise ValueError(f"Unsupported format: {fmt}")

    @property
    def json(self):
        return self.export('json')

    @json.setter
    def json(self, json_string):
        from .formats._json import import_book
        imported = import_book(json_string)
        self._datasets = imported._datasets
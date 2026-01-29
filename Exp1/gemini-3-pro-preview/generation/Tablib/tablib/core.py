import tablib.formats._csv as _csv
import tablib.formats._json as _json

class Dataset:
    def __init__(self, *rows, headers=None, title=None):
        self._data = [list(row) for row in rows]
        self._headers = list(headers) if headers else []
        self.title = title

    @property
    def headers(self):
        return self._headers

    @headers.setter
    def headers(self, value):
        self._headers = list(value)

    @property
    def height(self):
        return len(self._data)

    @property
    def width(self):
        if self._data:
            return len(self._data[0])
        if self._headers:
            return len(self._headers)
        return 0

    def __getitem__(self, key):
        if isinstance(key, slice):
            return [tuple(row) for row in self._data[key]]
        if isinstance(key, int):
            return tuple(self._data[key])
        if isinstance(key, str):
            if key not in self._headers:
                raise KeyError(key)
            idx = self._headers.index(key)
            return [row[idx] for row in self._data]
        raise TypeError("Invalid argument type.")

    def append(self, row):
        self._data.append(list(row))

    def append_col(self, values, header=None):
        if self._data and len(values) != len(self._data):
             raise ValueError("Column length must match dataset height")
        
        if not self._data:
            self._data = [[v] for v in values]
        else:
            for i, row in enumerate(self._data):
                row.append(values[i])
        
        if header is not None:
            if not self._headers and self.width > 1:
                self._headers = [''] * (self.width - 1)
            self._headers.append(header)
        elif self._headers:
            self._headers.append('')

    @property
    def dict(self):
        if not self._headers:
            raise ValueError("Headers required for dict property")
        return [dict(zip(self._headers, row)) for row in self._data]

    def export(self, fmt):
        if fmt == 'csv':
            return _csv.export_set(self)
        if fmt == 'json':
            return _json.export_set(self)
        raise ValueError(f"Unsupported format {fmt}")

    @property
    def csv(self):
        return self.export('csv')

    @csv.setter
    def csv(self, value):
        _csv.import_set(self, value)

    @property
    def json(self):
        return self.export('json')

    @json.setter
    def json(self, value):
        _json.import_set(self, value)

    def wipe(self):
        self._data = []
        self._headers = []

    def __len__(self):
        return self.height

    def __iter__(self):
        for row in self._data:
            yield tuple(row)


class Databook:
    def __init__(self, datasets=None):
        self._datasets = list(datasets) if datasets else []

    @property
    def size(self):
        return len(self._datasets)

    def sheets(self):
        return self._datasets

    def __iter__(self):
        return iter(self._datasets)

    def add_sheet(self, dataset):
        self._datasets.append(dataset)

    def export(self, fmt):
        if fmt == 'json':
            return _json.export_book(self)
        raise ValueError(f"Unsupported format {fmt}")

    @property
    def json(self):
        return self.export('json')

    @json.setter
    def json(self, value):
        _json.import_book(self, value)
    
    def wipe(self):
        self._datasets = []
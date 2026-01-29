import json

class Dataset:
    """A container for tabular data."""

    def __init__(self, *rows, headers=None):
        self._headers = list(headers) if headers is not None else []
        self._data = []
        self.title = None
        for row in rows:
            self.append(row)

    def __len__(self):
        return self.height

    def __getitem__(self, key):
        if isinstance(key, str):
            try:
                index = self._headers.index(key)
                return tuple(row[index] for row in self._data)
            except ValueError:
                raise KeyError(f"Column '{key}' not found in headers.")
        elif isinstance(key, slice):
            return [tuple(row) for row in self._data[key]]
        elif isinstance(key, int):
            return tuple(self._data[key])
        else:
            raise TypeError("Dataset indices must be integers, slices, or strings.")

    @property
    def headers(self):
        return self._headers

    @headers.setter
    def headers(self, value):
        new_headers = list(value) if value is not None else []
        old_width = self.width
        new_width = len(new_headers)
        
        if new_width != old_width:
            diff = new_width - old_width
            if diff > 0:
                for row in self._data:
                    row.extend([None] * diff)
            else:
                for i, row in enumerate(self._data):
                    self._data[i] = row[:new_width]

        self._headers = new_headers

    @property
    def height(self):
        return len(self._data)

    @property
    def width(self):
        return len(self._headers)

    def append(self, row):
        row_list = list(row)
        width = self.width
        
        if len(row_list) < width:
            row_list.extend([None] * (width - len(row_list)))
        elif len(row_list) > width:
            row_list = row_list[:width]
            
        self._data.append(row_list)

    def append_col(self, col, header=None):
        col_list = list(col)
        height = self.height

        if len(col_list) < height:
            col_list.extend([None] * (height - len(col_list)))
        elif len(col_list) > height:
            col_list = col_list[:height]

        self._headers.append(header)
        for i, val in enumerate(col_list):
            self._data[i].append(val)

    @property
    def dict(self):
        return [dict(zip(self.headers, row)) for row in self._data]

    def export(self, fmt):
        fmt = fmt.lower()
        if fmt == 'csv':
            from .formats import _csv
            return _csv.export_set(self)
        elif fmt == 'json':
            from .formats import _json
            return _json.export_set(self)
        else:
            raise NotImplementedError(f"Format '{fmt}' is not supported for export.")

    def wipe(self):
        """Clears all data and headers."""
        self._data = []
        self._headers = []

    def _load_from_dict_list(self, data):
        self.wipe()
        if not data or not isinstance(data, list):
            return

        self.headers = list(data[0].keys())
        
        for row_dict in data:
            row = [row_dict.get(h) for h in self.headers]
            self._data.append(row)

    @property
    def csv(self):
        return self.export('csv')

    @csv.setter
    def csv(self, value):
        from .formats import _csv
        _csv.import_set(self, value)

    @property
    def json(self):
        return self.export('json')

    @json.setter
    def json(self, value):
        from .formats import _json
        _json.import_set(self, value)


class Databook:
    """A container for multiple Datasets."""

    def __init__(self, datasets=None):
        self._sheets = list(datasets) if datasets is not None else []

    def __iter__(self):
        return iter(self._sheets)

    @property
    def size(self):
        return len(self._sheets)

    def sheets(self):
        return self._sheets

    def export(self, fmt):
        fmt = fmt.lower()
        if fmt == 'json':
            from .formats import _json
            return _json.export_book(self)
        else:
            raise NotImplementedError(f"Format '{fmt}' is not supported for export.")

    @property
    def json(self):
        return self.export('json')

    @json.setter
    def json(self, value):
        from .formats import _json
        _json.import_book(self, value)
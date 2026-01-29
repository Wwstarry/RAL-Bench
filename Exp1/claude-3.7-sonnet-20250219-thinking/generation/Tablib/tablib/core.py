from tablib.formats import _csv, _json

class Dataset:
    """A tabular dataset."""

    def __init__(self, *args, **kwargs):
        self.title = kwargs.get('title', None)
        self._headers = list(kwargs.get('headers', []))
        self._data = []
        
        # Add rows if provided
        for row in args:
            self.append(row)
    
    @property
    def headers(self):
        return self._headers
    
    @headers.setter
    def headers(self, value):
        self._headers = list(value) if value else []
    
    @property
    def height(self):
        return len(self._data)
    
    @property
    def width(self):
        if self._headers:
            return len(self._headers)
        elif self._data:
            return len(self._data[0])
        return 0
    
    def append(self, row):
        """Appends a row to the dataset."""
        self._data.append(tuple(row))
    
    def append_col(self, values, header=None):
        """Appends a column to the dataset."""
        if header is not None:
            self._headers.append(header)
        elif self._headers:
            # Maintain header alignment if headers exist but none provided
            self._headers.append("")
            
        # Make sure values is the right length
        if len(self._data) > 0 and len(values) != len(self._data):
            raise ValueError(f'Column length {len(values)} does not match dataset height {len(self._data)}')
        
        # Add values to each row
        if not self._data:
            for v in values:
                self._data.append((v,))
        else:
            for i, row in enumerate(self._data):
                self._data[i] = row + (values[i],)
    
    def __getitem__(self, key):
        """Enables slicing and column access."""
        if isinstance(key, slice):
            return self._data[key]
        elif isinstance(key, int):
            return self._data[key]
        elif isinstance(key, str):
            # Get column by header name
            if not self._headers:
                raise KeyError(f'Column header "{key}" not found')
            
            try:
                idx = self._headers.index(key)
                return [row[idx] for row in self._data]
            except ValueError:
                raise KeyError(f'Column header "{key}" not found')
        else:
            raise TypeError(f'Invalid key type: {type(key)}')
    
    @property
    def dict(self):
        """Returns a list of dictionaries, each representing a row."""
        if not self._headers:
            return []
        
        return [dict(zip(self._headers, row)) for row in self._data]
    
    def export(self, fmt):
        """Exports the dataset to the specified format."""
        if fmt == 'csv':
            return _csv.export_set(self)
        elif fmt == 'json':
            return _json.export_set(self)
        else:
            raise ValueError(f'Unsupported format: {fmt}')
    
    @property
    def csv(self):
        """CSV representation of the dataset."""
        return _csv.export_set(self)
    
    @csv.setter
    def csv(self, value):
        """Import CSV data."""
        headers, data = _csv.import_set(value)
        self._headers = headers
        self._data = data
    
    @property
    def json(self):
        """JSON representation of the dataset."""
        return _json.export_set(self)
    
    @json.setter
    def json(self, value):
        """Import JSON data."""
        headers, data = _json.import_set(value)
        self._headers = headers
        self._data = data


class Databook:
    """A book of tabular datasets."""
    
    def __init__(self, datasets=None):
        self._datasets = []
        if datasets:
            for dataset in datasets:
                self._datasets.append(dataset)
    
    @property
    def size(self):
        """Number of datasets in the databook."""
        return len(self._datasets)
    
    def sheets(self):
        """Returns an iterator of datasets."""
        return iter(self._datasets)
    
    def __iter__(self):
        """Enables iteration over datasets."""
        return self.sheets()
    
    def export(self, fmt):
        """Exports the databook to the specified format."""
        if fmt == 'json':
            return _json.export_book(self)
        else:
            raise ValueError(f'Unsupported format for Databook: {fmt}')
    
    @property
    def json(self):
        """JSON representation of the databook."""
        return _json.export_book(self)
    
    @json.setter
    def json(self, value):
        """Import JSON data into the databook."""
        self._datasets = _json.import_book(value)
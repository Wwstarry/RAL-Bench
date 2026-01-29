"""Core tablib classes."""
import json
from collections import defaultdict
from typing import Any, Iterable, Iterator, List, Optional, Sequence, Tuple, Union


class Dataset:
    """Tabular dataset container."""
    
    def __init__(self, *rows: Iterable, headers: Optional[Iterable] = None):
        self._data: List[List[Any]] = []
        self._headers: List[str] = []
        
        if headers is not None:
            self.headers = list(headers)
        
        for row in rows:
            self.append(row)
    
    @property
    def headers(self) -> List[str]:
        """Get or set column headers."""
        return self._headers.copy()
    
    @headers.setter
    def headers(self, value: Iterable):
        if not value:
            self._headers = []
            return
        
        headers_list = list(value)
        current_width = self.width
        
        # If setting headers for the first time and we have data,
        # ensure we have enough headers
        if current_width > 0 and len(self._headers) == 0:
            if len(headers_list) < current_width:
                # Pad with empty headers
                headers_list.extend([''] * (current_width - len(headers_list)))
            elif len(headers_list) > current_width:
                # Truncate extra headers
                headers_list = headers_list[:current_width]
        
        self._headers = [str(h) for h in headers_list]
    
    @property
    def height(self) -> int:
        """Number of rows in the dataset."""
        return len(self._data)
    
    @property
    def width(self) -> int:
        """Number of columns in the dataset."""
        if self._data:
            return len(self._data[0])
        return len(self._headers) if self._headers else 0
    
    def __len__(self) -> int:
        return self.height
    
    def __getitem__(self, key: Union[int, slice, str]) -> Any:
        """Get rows by slice, or column by header name."""
        if isinstance(key, str):
            return self._get_column(key)
        elif isinstance(key, slice):
            return self._get_slice(key)
        elif isinstance(key, int):
            if key < 0:
                key = self.height + key
            if 0 <= key < self.height:
                return tuple(self._data[key])
            raise IndexError("Row index out of range")
        else:
            raise TypeError("Invalid key type")
    
    def _get_slice(self, slice_obj: slice) -> List[Tuple]:
        """Get rows as tuples for the given slice."""
        start, stop, step = slice_obj.indices(self.height)
        return [tuple(self._data[i]) for i in range(start, stop, step)]
    
    def _get_column(self, header: str) -> List[Any]:
        """Get all values for a column by header name."""
        if not self._headers:
            raise KeyError(f"No headers defined")
        
        try:
            col_idx = self._headers.index(header)
        except ValueError:
            raise KeyError(f"Column '{header}' not found")
        
        return [row[col_idx] for row in self._data]
    
    def append(self, row: Iterable):
        """Append a row to the dataset."""
        row_list = list(row)
        
        if self.height == 0:
            # First row determines width
            self._data.append(row_list)
            return
        
        current_width = self.width
        row_len = len(row_list)
        
        if row_len < current_width:
            # Pad with empty values
            row_list.extend([''] * (current_width - row_len))
        elif row_len > current_width:
            # Truncate extra values
            row_list = row_list[:current_width]
        
        self._data.append(row_list)
    
    def append_col(self, values: Iterable, header: Optional[str] = None):
        """Append a column to the dataset."""
        values_list = list(values)
        
        if self.height > 0 and len(values_list) != self.height:
            raise ValueError(
                f"Values length ({len(values_list)}) must match dataset height ({self.height})"
            )
        
        # Add header
        if header is not None:
            if self._headers is None:
                self._headers = []
            self._headers.append(str(header))
        elif self._headers:
            # Add empty header if headers exist
            self._headers.append('')
        
        # Add values to each row
        if self.height == 0:
            # Dataset is empty, create rows from values
            self._data = [[v] for v in values_list]
        else:
            for i, value in enumerate(values_list):
                self._data[i].append(value)
    
    @property
    def dict(self) -> List[dict]:
        """Get dataset as list of dictionaries."""
        if not self._headers:
            # If no headers, return list of tuples
            return [dict(enumerate(row)) for row in self._data]
        
        result = []
        for row in self._data:
            row_dict = {}
            for i, header in enumerate(self._headers):
                if i < len(row):
                    row_dict[header] = row[i]
                else:
                    row_dict[header] = ''
            result.append(row_dict)
        return result
    
    def export(self, fmt: str) -> str:
        """Export dataset to specified format."""
        if fmt == 'csv':
            from .formats._csv import export_csv
            return export_csv(self)
        elif fmt == 'json':
            from .formats._json import export_json
            return export_json(self)
        else:
            raise ValueError(f"Unsupported format: {fmt}")
    
    @property
    def csv(self) -> str:
        """Get or set CSV representation."""
        return self.export('csv')
    
    @csv.setter
    def csv(self, value: str):
        from .formats._csv import import_csv
        imported = import_csv(value)
        self._data = imported._data
        self._headers = imported._headers
    
    @property
    def json(self) -> str:
        """Get or set JSON representation."""
        return self.export('json')
    
    @json.setter
    def json(self, value: str):
        from .formats._json import import_json
        imported = import_json(value)
        self._data = imported._data
        self._headers = imported._headers
    
    def __repr__(self) -> str:
        return f"<Dataset height={self.height}, width={self.width}>"


class Databook:
    """Collection of datasets (sheets)."""
    
    def __init__(self, datasets: Optional[Iterable[Dataset]] = None):
        self._sheets: List[Dataset] = []
        if datasets:
            for ds in datasets:
                self.add_sheet(ds)
    
    def add_sheet(self, dataset: Dataset):
        """Add a dataset as a sheet."""
        if not hasattr(dataset, 'title'):
            dataset.title = f"Sheet{self.size + 1}"
        self._sheets.append(dataset)
    
    @property
    def size(self) -> int:
        """Number of sheets in the databook."""
        return len(self._sheets)
    
    def sheets(self) -> List[Dataset]:
        """Get list of sheets."""
        return self._sheets.copy()
    
    def __iter__(self) -> Iterator[Dataset]:
        return iter(self._sheets)
    
    def __len__(self) -> int:
        return self.size
    
    def export(self, fmt: str) -> str:
        """Export databook to specified format."""
        if fmt == 'json':
            from .formats._json import export_book_json
            return export_book_json(self)
        else:
            raise ValueError(f"Unsupported format: {fmt}")
    
    @property
    def json(self) -> str:
        """Get or set JSON representation."""
        return self.export('json')
    
    @json.setter
    def json(self, value: str):
        from .formats._json import import_book_json
        imported = import_book_json(value)
        self._sheets = imported._sheets
    
    def __repr__(self) -> str:
        return f"<Databook sheets={self.size}>"
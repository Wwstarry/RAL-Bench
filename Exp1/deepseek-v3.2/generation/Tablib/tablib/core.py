"""Core tablib classes."""
import json
import csv
import io
from typing import Any, Iterable, List, Dict, Optional, Union, Iterator


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
        return self._headers
    
    @headers.setter
    def headers(self, value: Iterable):
        """Set column headers."""
        if value is None:
            self._headers = []
        else:
            self._headers = list(value)
        
        # Ensure data width matches headers
        if self._headers and self._data:
            current_width = len(self._headers)
            for i in range(len(self._data)):
                if len(self._data[i]) < current_width:
                    self._data[i].extend([None] * (current_width - len(self._data[i])))
                elif len(self._data[i]) > current_width:
                    self._data[i] = self._data[i][:current_width]
    
    @property
    def height(self) -> int:
        """Number of rows."""
        return len(self._data)
    
    @property
    def width(self) -> int:
        """Number of columns."""
        if self._headers:
            return len(self._headers)
        elif self._data:
            return len(self._data[0]) if self._data else 0
        return 0
    
    def __len__(self) -> int:
        return self.height
    
    def __getitem__(self, key: Union[int, slice, str]) -> Any:
        """Get rows by slice, or column by name."""
        if isinstance(key, slice):
            # Return row tuples for the slice
            return [tuple(row) for row in self._data[key]]
        elif isinstance(key, str):
            # Return column values
            if key not in self._headers:
                raise KeyError(f"Column '{key}' not found")
            col_idx = self._headers.index(key)
            return [row[col_idx] if col_idx < len(row) else None for row in self._data]
        elif isinstance(key, int):
            # Return single row as tuple
            return tuple(self._data[key])
        else:
            raise TypeError(f"Invalid key type: {type(key)}")
    
    def append(self, row: Iterable):
        """Append a row to the dataset."""
        row_list = list(row)
        
        # Ensure row has correct width
        if self._headers:
            expected_width = len(self._headers)
            if len(row_list) < expected_width:
                row_list.extend([None] * (expected_width - len(row_list)))
            elif len(row_list) > expected_width:
                row_list = row_list[:expected_width]
        elif self._data:
            # If we have data but no headers, ensure consistent width
            expected_width = len(self._data[0])
            if len(row_list) < expected_width:
                row_list.extend([None] * (expected_width - len(row_list)))
            elif len(row_list) > expected_width:
                # Update all existing rows to match new width
                for i in range(len(self._data)):
                    self._data[i].extend([None] * (len(row_list) - len(self._data[i])))
        
        self._data.append(row_list)
    
    def append_col(self, values: Iterable, header: Optional[str] = None):
        """Append a column to the dataset."""
        values_list = list(values)
        
        # Ensure values match height
        if len(values_list) < self.height:
            values_list.extend([None] * (self.height - len(values_list)))
        elif len(values_list) > self.height:
            # Pad existing rows
            for i in range(self.height):
                self._data[i].append(values_list[i])
            # Add new rows for extra values
            for i in range(self.height, len(values_list)):
                new_row = [None] * (self.width)
                new_row.append(values_list[i])
                self._data.append(new_row)
        else:
            # Values match height exactly
            for i in range(self.height):
                self._data[i].append(values_list[i])
        
        # Update headers
        if header is None:
            header = f"Column {self.width}"
        
        # If we're adding the first column to an empty dataset
        if not self._headers and self._data:
            self._headers = [header]
        else:
            self._headers.append(header)
    
    @property
    def dict(self) -> List[Dict[str, Any]]:
        """Return dataset as list of dictionaries."""
        if not self._headers:
            return []
        
        result = []
        for row in self._data:
            row_dict = {}
            for i, header in enumerate(self._headers):
                row_dict[header] = row[i] if i < len(row) else None
            result.append(row_dict)
        return result
    
    def export(self, fmt: str) -> str:
        """Export dataset to specified format."""
        if fmt == 'csv':
            return self.csv
        elif fmt == 'json':
            return self.json
        else:
            raise ValueError(f"Unsupported format: {fmt}")
    
    @property
    def csv(self) -> str:
        """Get dataset as CSV string."""
        output = io.StringIO()
        writer = csv.writer(output)
        
        if self._headers:
            writer.writerow(self._headers)
        
        for row in self._data:
            writer.writerow(row)
        
        return output.getvalue()
    
    @csv.setter
    def csv(self, value: str):
        """Import dataset from CSV string."""
        input_stream = io.StringIO(value)
        reader = csv.reader(input_stream)
        
        self._data = []
        self._headers = []
        
        try:
            # First row might be headers
            first_row = next(reader)
            self._headers = first_row
            self._data.append(list(first_row))
        except StopIteration:
            return
        
        # Read remaining rows
        for row in reader:
            self._data.append(row)
        
        # If first row was actually data (no headers), move it to data
        if self._data and self._data[0] == self._headers:
            # Check if first row looks like headers (all strings) vs data
            # Simple heuristic: if all values in first row are strings and match pattern
            # For simplicity, we'll assume first row is headers
            pass
    
    @property
    def json(self) -> str:
        """Get dataset as JSON string."""
        return json.dumps(self.dict, indent=2)
    
    @json.setter
    def json(self, value: str):
        """Import dataset from JSON string."""
        data = json.loads(value)
        
        if not data:
            self._data = []
            self._headers = []
            return
        
        # Determine headers from first dictionary
        first_dict = data[0]
        self._headers = list(first_dict.keys())
        
        # Extract data
        self._data = []
        for item in data:
            row = [item.get(header) for header in self._headers]
            self._data.append(row)
    
    def __iter__(self) -> Iterator[tuple]:
        """Iterate over rows as tuples."""
        for row in self._data:
            yield tuple(row)
    
    def __repr__(self) -> str:
        return f"<Dataset height={self.height} width={self.width}>"


class Databook:
    """Collection of datasets."""
    
    def __init__(self, datasets: Optional[Iterable[Dataset]] = None):
        self._datasets: List[Dataset] = []
        if datasets:
            for ds in datasets:
                self.add_sheet(ds)
    
    def add_sheet(self, dataset: Dataset):
        """Add a dataset to the book."""
        self._datasets.append(dataset)
    
    @property
    def size(self) -> int:
        """Number of sheets in the book."""
        return len(self._datasets)
    
    def sheets(self) -> List[Dataset]:
        """Get list of sheets."""
        return self._datasets
    
    def __iter__(self) -> Iterator[Dataset]:
        """Iterate over sheets."""
        return iter(self._datasets)
    
    def __len__(self) -> int:
        return self.size
    
    def export(self, fmt: str) -> str:
        """Export databook to specified format."""
        if fmt == 'json':
            return self.json
        else:
            raise ValueError(f"Unsupported format: {fmt}")
    
    @property
    def json(self) -> str:
        """Get databook as JSON string."""
        book_data = []
        for i, dataset in enumerate(self._datasets):
            sheet_data = {
                'title': getattr(dataset, 'title', f"Sheet{i+1}"),
                'headers': dataset.headers,
                'data': dataset._data
            }
            book_data.append(sheet_data)
        return json.dumps(book_data, indent=2)
    
    @json.setter
    def json(self, value: str):
        """Import databook from JSON string."""
        book_data = json.loads(value)
        
        self._datasets = []
        for sheet_data in book_data:
            dataset = Dataset()
            dataset.title = sheet_data.get('title', '')
            dataset.headers = sheet_data.get('headers', [])
            dataset._data = sheet_data.get('data', [])
            self._datasets.append(dataset)
    
    def __repr__(self) -> str:
        return f"<Databook size={self.size}>"
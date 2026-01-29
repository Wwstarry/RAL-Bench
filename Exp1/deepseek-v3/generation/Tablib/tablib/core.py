"""Core tablib functionality."""
import json
import csv
import io
from typing import List, Dict, Any, Optional, Union, Iterator

class Dataset:
    """A dataset represents a tabular data structure with headers and rows."""
    
    def __init__(self, *rows, headers: Optional[List[str]] = None):
        self._headers = list(headers) if headers else []
        self._data = []
        
        # Add rows if provided
        for row in rows:
            self.append(row)
    
    @property
    def headers(self) -> List[str]:
        """Get or set the column headers."""
        return self._headers
    
    @headers.setter
    def headers(self, value: List[str]):
        """Set the column headers."""
        if not value:
            self._headers = []
            return
            
        # Ensure headers are strings
        self._headers = [str(h) for h in value]
        
        # If we have data but headers are changing width, clear data
        if self._data and len(self._headers) != len(self._data[0]):
            self._data = []
    
    @property
    def height(self) -> int:
        """Number of rows in the dataset."""
        return len(self._data)
    
    @property
    def width(self) -> int:
        """Number of columns in the dataset."""
        return len(self._headers) if self._headers else (len(self._data[0]) if self._data else 0)
    
    def append(self, row) -> None:
        """Append a row to the dataset."""
        if not row:
            return
            
        row_list = list(row)
        
        # Initialize headers if this is the first row and no headers set
        if not self._headers and not self._data:
            self._headers = [f"Column_{i+1}" for i in range(len(row_list))]
        
        # Validate row length matches headers
        if self._headers and len(row_list) != len(self._headers):
            raise ValueError(f"Row length {len(row_list)} doesn't match headers length {len(self._headers)}")
        
        self._data.append([str(cell) if cell is not None else "" for cell in row_list])
    
    def append_col(self, values: List, header: Optional[str] = None) -> None:
        """Append a column to the dataset."""
        if not values:
            return
            
        if len(values) != self.height:
            raise ValueError(f"Values length {len(values)} doesn't match dataset height {self.height}")
        
        # Add header
        if header is None:
            header = f"Column_{self.width + 1}"
        
        self._headers.append(str(header))
        
        # Add values to each row
        for i, value in enumerate(values):
            if i < len(self._data):
                self._data[i].append(str(value) if value is not None else "")
    
    def __getitem__(self, key: Union[int, slice, str]) -> Union[tuple, List[tuple], List[str]]:
        """Get rows by slice or column by name."""
        if isinstance(key, slice):
            # Slice rows
            return [tuple(row) for row in self._data[key]]
        elif isinstance(key, str):
            # Column access
            if key not in self._headers:
                raise KeyError(f"Column '{key}' not found in headers")
            col_index = self._headers.index(key)
            return [row[col_index] for row in self._data]
        else:
            # Single row access
            return tuple(self._data[key])
    
    def __len__(self) -> int:
        """Number of rows."""
        return self.height
    
    @property
    def dict(self) -> List[Dict[str, str]]:
        """Return dataset as list of dictionaries."""
        if not self._headers or not self._data:
            return []
        
        return [
            {header: value for header, value in zip(self._headers, row)}
            for row in self._data
        ]
    
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
        
        writer.writerows(self._data)
        return output.getvalue()
    
    @csv.setter
    def csv(self, value: str) -> None:
        """Set dataset from CSV string."""
        if not value:
            self._headers = []
            self._data = []
            return
            
        input_io = io.StringIO(value.strip())
        reader = csv.reader(input_io)
        
        rows = list(reader)
        if not rows:
            self._headers = []
            self._data = []
            return
        
        # First row is headers
        self._headers = [str(h) for h in rows[0]]
        self._data = []
        
        # Remaining rows are data
        for row in rows[1:]:
            if row:  # Skip empty rows
                self._data.append([str(cell) if cell else "" for cell in row])
    
    @property
    def json(self) -> str:
        """Get dataset as JSON string."""
        return json.dumps(self.dict, indent=2)
    
    @json.setter
    def json(self, value: str) -> None:
        """Set dataset from JSON string."""
        if not value:
            self._headers = []
            self._data = []
            return
            
        data = json.loads(value)
        if not data:
            self._headers = []
            self._data = []
            return
        
        if isinstance(data, list) and data and isinstance(data[0], dict):
            # List of dictionaries format
            self._headers = list(data[0].keys()) if data else []
            self._data = []
            
            for row_dict in data:
                row = []
                for header in self._headers:
                    value = row_dict.get(header, "")
                    row.append(str(value) if value is not None else "")
                self._data.append(row)
        else:
            raise ValueError("Invalid JSON format for dataset")


class Databook:
    """A collection of datasets (sheets)."""
    
    def __init__(self, datasets=None):
        self._datasets = list(datasets) if datasets else []
    
    @property
    def size(self) -> int:
        """Number of sheets in the databook."""
        return len(self._datasets)
    
    def sheets(self) -> List[Dataset]:
        """Get all sheets."""
        return self._datasets
    
    def __iter__(self) -> Iterator[Dataset]:
        """Iterate over sheets."""
        return iter(self._datasets)
    
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
        for dataset in self._datasets:
            sheet_data = {
                'title': getattr(dataset, 'title', 'Sheet'),
                'headers': dataset.headers,
                'data': dataset._data
            }
            book_data.append(sheet_data)
        
        return json.dumps(book_data, indent=2)
    
    @json.setter
    def json(self, value: str) -> None:
        """Set databook from JSON string."""
        if not value:
            self._datasets = []
            return
            
        book_data = json.loads(value)
        if not isinstance(book_data, list):
            raise ValueError("Invalid JSON format for databook")
        
        self._datasets = []
        for sheet_data in book_data:
            dataset = Dataset()
            
            # Set title if present
            if 'title' in sheet_data:
                dataset.title = sheet_data['title']
            
            # Set headers and data
            if 'headers' in sheet_data and 'data' in sheet_data:
                dataset.headers = sheet_data['headers']
                dataset._data = [
                    [str(cell) if cell is not None else "" for cell in row]
                    for row in sheet_data['data']
                ]
            
            self._datasets.append(dataset)
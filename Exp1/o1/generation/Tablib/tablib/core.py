import typing

from .formats import _csv as csv_format
from .formats import _json as json_format


class Dataset:
    """
    A minimal Dataset implementation exposing the core API needed for tests.
    """

    def __init__(self, *rows, headers=None):
        """
        Initialize the Dataset.

        :param rows: zero or more row iterables
        :param headers: an iterable of column names
        """
        self._headers = list(headers) if headers else []
        self._data = []
        self.title = None  # optional title field

        for row in rows:
            self.append(row)

    @property
    def headers(self):
        return self._headers

    @headers.setter
    def headers(self, value):
        # Ensure new headers match existing width if we already have data
        if self._data and len(value) != self.width:
            raise ValueError("New headers must match the current data width.")
        self._headers = list(value)

    @property
    def height(self):
        return len(self._data)

    @property
    def width(self):
        return len(self._headers)

    def __getitem__(self, key):
        """
        - If key is a slice, return a list of row tuples (start:stop).
        - If key is a string, return the column data for that header.
        """
        if isinstance(key, slice):
            return [tuple(row) for row in self._data[key]]
        elif isinstance(key, str):
            if key not in self._headers:
                raise KeyError(f"Column '{key}' does not exist in headers.")
            col_idx = self._headers.index(key)
            return [row[col_idx] for row in self._data]
        else:
            raise TypeError("Dataset indices must be slice or str (column name).")

    def append(self, row):
        """
        Append a single row.
        """
        row = list(row)
        # If we have headers, row must match the width
        if self._headers:
            if len(row) != self.width:
                raise ValueError("Row length does not match the number of headers.")
        else:
            # if no headers exist yet, set them to match the incoming row length
            self._headers = [f"untitled_{i}" for i in range(len(row))]
        self._data.append(row)

    def append_col(self, values, header=None):
        """
        Append a column with optional header. Values must match current height.
        """
        values = list(values)
        if len(values) != self.height:
            raise ValueError("Number of values does not match dataset height.")
        if header is None:
            header = f"untitled_{self.width}"
        self._headers.append(header)

        for row_idx, val in enumerate(values):
            self._data[row_idx].append(val)

    def export(self, fmt: str) -> str:
        """
        Export this dataset to a string in the requested format ('csv' or 'json').
        """
        if fmt == "csv":
            return csv_format.export_set(self)
        elif fmt == "json":
            return json_format.export_set(self)
        else:
            raise ValueError(f"Unsupported format '{fmt}'.")

    @property
    def csv(self) -> str:
        """
        Return a CSV-formatted string of the dataset.
        """
        return self.export("csv")

    @csv.setter
    def csv(self, data: str):
        """
        Overwrite dataset content from a CSV-formatted string.
        """
        csv_format.import_set(self, data)

    @property
    def json(self) -> str:
        """
        Return a JSON-formatted string of the dataset.
        """
        return self.export("json")

    @json.setter
    def json(self, data: str):
        """
        Overwrite dataset content from a JSON-formatted string.
        """
        json_format.import_set(self, data)

    @property
    def dict(self) -> typing.List[typing.Dict[str, typing.Any]]:
        """
        Return a list of dictionaries, one per row, mapping header names to cell values.
        """
        output = []
        for row in self._data:
            row_dict = {}
            for i, header in enumerate(self._headers):
                row_dict[header] = row[i]
            output.append(row_dict)
        return output


class Databook:
    """
    A minimal Databook implementation exposing the core API used by the tests.
    """

    def __init__(self, datasets=None):
        self._datasets = []
        if datasets:
            for d in datasets:
                self._datasets.append(d)

    @property
    def size(self):
        return len(self._datasets)

    def sheets(self):
        return self._datasets

    def __iter__(self):
        return iter(self._datasets)

    def export(self, fmt: str) -> str:
        """
        Export the entire databook to a string in the requested format ('json' only).
        """
        if fmt == "json":
            return json_format.export_book(self)
        else:
            raise ValueError(f"Unsupported format '{fmt}' for Databook.")

    @property
    def json(self) -> str:
        """
        Return a JSON-formatted string for the entire book.
        """
        return self.export("json")

    @json.setter
    def json(self, data: str):
        """
        Overwrite book content from a JSON-formatted string.
        """
        json_format.import_book(self, data)
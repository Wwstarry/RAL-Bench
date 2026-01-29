"""
Core implementation of the lightweight Tablib clone.

Only the subset of behaviour required by the test-suite is implemented.
"""

from __future__ import annotations

import copy
import json
from typing import Iterable, List, Sequence, Tuple, Iterator, Any, Optional

from .formats import _csv as csv_format
from .formats import _json as json_format


###############################################################################
# Helper utilities
###############################################################################


def _ensure_sequence(obj, message: str = "Expected an iterable") -> List[Any]:
    """Coerce *obj* to an in-memory list.

    This helper is used to materialise iterables that could otherwise be
    exhausted by subsequent iterations and to provide friendly error messages
    when a scalar is accidentally supplied.
    """
    if obj is None:
        return []
    if isinstance(obj, (str, bytes)):
        raise TypeError(message)
    try:
        return list(obj)
    except TypeError:
        raise TypeError(message) from None


###############################################################################
# Dataset
###############################################################################


class Dataset:
    """Two-dimensional tabular data container."""

    #######################################################################
    # Construction
    #######################################################################

    def __init__(self, *rows: Iterable[Any], headers: Optional[Iterable[str]] = None):
        """
        Parameters
        ----------
        *rows
            Positional arguments represent the initial rows for the dataset.
            Each row must itself be an iterable.

        headers
            Optional iterable of column names.
        """
        self._headers: Optional[List[str]] = (
            list(headers) if headers is not None else None
        )
        self._rows: List[List[Any]] = [list(r) for r in rows]

        # Validate consistency between header width and row widths.
        if self._headers is not None:
            for row in self._rows:
                if len(row) != len(self._headers):
                    raise ValueError("Row length does not match header length")

    #######################################################################
    # Basic properties
    #######################################################################

    @property
    def headers(self) -> Optional[List[str]]:
        """Return the header sequence (or *None* when not set)."""
        return copy.copy(self._headers) if self._headers is not None else None

    @headers.setter
    def headers(self, value: Optional[Iterable[str]]):
        if value is None:
            self._headers = None
            return
        headers = list(value)
        if self.width and len(headers) != self.width:
            raise ValueError("Header length must match existing width")
        self._headers = headers

    @property
    def height(self) -> int:
        """Number of rows."""
        return len(self._rows)

    @property
    def width(self) -> int:
        """Number of columns."""
        if self._headers is not None:
            return len(self._headers)
        if self._rows:
            return len(self._rows[0])
        return 0

    #######################################################################
    # Core data access
    #######################################################################

    def __len__(self) -> int:  # Allows `len(dataset)`
        return self.height

    def __iter__(self) -> Iterator[Tuple[Any, ...]]:
        for row in self._rows:
            yield tuple(row)

    def __getitem__(self, key):
        """Row access (integer or slice) or column access (string header)."""
        if isinstance(key, slice) or isinstance(key, int):
            result = self._rows[key]
            if isinstance(result, list):
                # slice -> list of rows
                return [tuple(r) for r in result]
            else:
                # single row (int index)
                return tuple(result)
        elif isinstance(key, str):
            if self._headers is None:
                raise KeyError("Dataset has no headers defined.")
            try:
                idx = self._headers.index(key)
            except ValueError:
                raise KeyError(key) from None
            return [row[idx] if idx < len(row) else None for row in self._rows]
        else:
            raise TypeError("Invalid key type for Dataset")

    #######################################################################
    # Mutation helpers
    #######################################################################

    def append(self, row: Iterable[Any]):
        row_list = list(row)
        if self.width and len(row_list) != self.width:
            raise ValueError("Row length must match dataset width")
        self._rows.append(row_list)

    def append_col(self, values: Iterable[Any], header: Optional[str] = None):
        values_list = _ensure_sequence(values, "values must be iterable")
        if self.height and len(values_list) != self.height:
            raise ValueError("Column length must match dataset height")
        if not self.height:
            # If dataset empty, create empty rows first
            for _ in range(len(values_list)):
                self._rows.append([])
        for row, value in zip(self._rows, values_list):
            row.append(value)

        # Update header
        if header is not None:
            if self._headers is None:
                self._headers = []
            self._headers.append(header)
        else:
            if self._headers is not None:
                self._headers.append(f"Column {len(self._headers)}")

    #######################################################################
    # Serialisation helpers
    #######################################################################

    def export(self, fmt: str) -> str:
        fmt = fmt.lower()
        if fmt == "csv":
            return csv_format.export_set(self)
        elif fmt == "json":
            return json_format.export_set(self)
        else:
            raise ValueError(f"Unsupported format {fmt!r}")

    # CSV property
    @property
    def csv(self) -> str:  # noqa: D401
        """Return CSV representation."""
        return self.export("csv")

    @csv.setter
    def csv(self, in_str: str):
        # Reset current content
        self._headers = None
        self._rows = []
        csv_format.import_set(self, in_str)

    # JSON property
    @property
    def json(self) -> str:
        return self.export("json")

    @json.setter
    def json(self, in_str: str):
        self._headers = None
        self._rows = []
        json_format.import_set(self, in_str)

    #######################################################################
    # Higher-level helpers
    #######################################################################

    @property
    def dict(self) -> List[dict]:
        """Return the dataset as a list of dictionaries (one per row)."""
        if not self._headers:
            # When no headers, fall back to integer keys.
            return [dict(enumerate(row)) for row in self._rows]
        output = []
        for row in self._rows:
            # Pad shorter rows with Nones
            padded = list(row) + [None] * (len(self._headers) - len(row))
            output.append(dict(zip(self._headers, padded)))
        return output

    #######################################################################
    # Misc helpers
    #######################################################################

    def __repr__(self):
        return f"<Dataset #rows={self.height} #cols={self.width}>"


###############################################################################
# Databook
###############################################################################


class Databook:
    """A lightweight container grouping multiple Dataset instances."""

    def __init__(self, datasets: Iterable[Dataset]):
        self._datasets: List[Dataset] = list(datasets)

    #######################################################################
    # Basic properties / iteration
    #######################################################################

    @property
    def size(self) -> int:
        return len(self._datasets)

    def __len__(self):
        return self.size

    def __iter__(self) -> Iterator[Dataset]:
        return iter(self._datasets)

    def sheets(self) -> List[Dataset]:
        """Return the datasets in the book in insertion order."""
        return list(self._datasets)

    #######################################################################
    # Serialisation
    #######################################################################

    def export(self, fmt: str) -> str:
        fmt = fmt.lower()
        if fmt != "json":
            raise ValueError("Databook currently supports only JSON export")
        serialisable = []
        for ds in self._datasets:
            serialisable.append(
                {
                    "title": getattr(ds, "title", None),
                    "headers": ds.headers,
                    "data": [list(r) for r in ds._rows],
                }
            )
        return json.dumps(serialisable)

    @property
    def json(self) -> str:
        return self.export("json")

    @json.setter
    def json(self, in_str: str):
        raw = json.loads(in_str)
        rebuilt = []
        for sheet in raw:
            data = sheet.get("data", [])
            headers = sheet.get("headers")
            ds = Dataset(*data, headers=headers)
            title = sheet.get("title")
            if title is not None:
                ds.title = title
            rebuilt.append(ds)
        self._datasets = rebuilt

    #######################################################################
    # Misc
    #######################################################################

    def __repr__(self):
        titles = [getattr(ds, "title", None) for ds in self._datasets]
        return f"<Databook size={self.size} titles={titles}>"
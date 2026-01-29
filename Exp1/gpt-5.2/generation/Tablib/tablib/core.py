from __future__ import annotations

import json
from typing import Any, Dict, Iterable, Iterator, List, Optional, Sequence, Tuple, Union

from .formats import _csv as csv_format
from .formats import _json as json_format


RowLike = Iterable[Any]


class Dataset:
    """
    Minimal tabular container compatible with the core API surface used in tests.
    """

    def __init__(self, *rows: RowLike, headers: Optional[Iterable[str]] = None) -> None:
        self.title: Optional[str] = None
        self._headers: Optional[List[str]] = list(headers) if headers is not None else None
        self._data: List[List[Any]] = []
        for r in rows:
            self.append(r)

    @property
    def headers(self) -> Optional[List[str]]:
        return list(self._headers) if self._headers is not None else None

    @headers.setter
    def headers(self, value: Optional[Iterable[str]]) -> None:
        self._headers = list(value) if value is not None else None
        # Do not coerce/resize existing data; Tablib tolerates mismatch.
        # Width is derived from headers if present; otherwise from data.

    @property
    def height(self) -> int:
        return len(self._data)

    @property
    def width(self) -> int:
        if self._headers is not None:
            return len(self._headers)
        if not self._data:
            return 0
        return max((len(r) for r in self._data), default=0)

    def _ensure_row_width(self, row: List[Any]) -> List[Any]:
        """
        Normalize a row to the dataset's current width when headers exist,
        or keep as-is if headers absent (width determined by max row length).
        """
        if self._headers is None:
            return row
        w = len(self._headers)
        if len(row) < w:
            row = row + [None] * (w - len(row))
        elif len(row) > w:
            row = row[:w]
        return row

    def append(self, row: RowLike) -> None:
        row_list = list(row)
        if self._headers is not None:
            row_list = self._ensure_row_width(row_list)
        self._data.append(row_list)

    def append_col(self, values: Iterable[Any], header: Optional[str] = None) -> None:
        vals = list(values)
        if self.height != 0 and len(vals) != self.height:
            raise ValueError("Column length must match dataset height.")
        if self.height == 0 and len(vals) > 0:
            # Create rows from column values
            self._data = [[v] for v in vals]
        else:
            # Add to each existing row
            for i in range(self.height):
                self._data[i].append(vals[i] if self.height else None)

        # Update headers if present or header explicitly given.
        if self._headers is None:
            if header is not None:
                # Create headers up to current width, with blanks then set last.
                self._headers = ["" for _ in range(self.width - 1)] + [header]
        else:
            self._headers.append(header if header is not None else "")

        # If headers exist, normalize all rows to header width.
        if self._headers is not None:
            for i in range(self.height):
                self._data[i] = self._ensure_row_width(self._data[i])

    def __getitem__(self, item: Union[slice, int, str]) -> Any:
        if isinstance(item, slice):
            return [tuple(r) for r in self._data[item]]
        if isinstance(item, str):
            # Column access by header name
            if self._headers is None:
                raise KeyError(item)
            try:
                idx = self._headers.index(item)
            except ValueError as e:
                raise KeyError(item) from e
            out = []
            for r in self._data:
                out.append(r[idx] if idx < len(r) else None)
            return out
        if isinstance(item, int):
            return tuple(self._data[item])
        raise TypeError("Invalid index type.")

    def __iter__(self) -> Iterator[Tuple[Any, ...]]:
        for r in self._data:
            yield tuple(r)

    @property
    def dict(self) -> List[Dict[str, Any]]:
        headers = self._headers
        if headers is None:
            # If no headers, behave like empty dicts for each row.
            return [{} for _ in self._data]
        out: List[Dict[str, Any]] = []
        for r in self._data:
            d: Dict[str, Any] = {}
            for i, h in enumerate(headers):
                d[h] = r[i] if i < len(r) else None
            out.append(d)
        return out

    def export(self, fmt: str) -> str:
        fmt = (fmt or "").lower()
        if fmt == "csv":
            return csv_format.export_dataset(self)
        if fmt == "json":
            return json_format.export_dataset(self)
        raise ValueError(f"Unsupported format: {fmt}")

    # CSV attribute-style access
    @property
    def csv(self) -> str:
        return self.export("csv")

    @csv.setter
    def csv(self, value: str) -> None:
        headers, rows = csv_format.import_dataset(value)
        self._headers = headers
        self._data = [list(r) for r in rows]

    # JSON attribute-style access
    @property
    def json(self) -> str:
        return self.export("json")

    @json.setter
    def json(self, value: str) -> None:
        headers, rows = json_format.import_dataset(value)
        self._headers = headers
        self._data = [list(r) for r in rows]


class Databook:
    """
    Minimal Databook compatible with tests: a collection of Dataset sheets.
    """

    def __init__(self, datasets: Optional[Iterable[Dataset]] = None) -> None:
        self._datasets: List[Dataset] = list(datasets) if datasets is not None else []

    @property
    def size(self) -> int:
        return len(self._datasets)

    def sheets(self) -> List[Dataset]:
        return list(self._datasets)

    def __iter__(self) -> Iterator[Dataset]:
        return iter(self._datasets)

    def export(self, fmt: str) -> str:
        fmt = (fmt or "").lower()
        if fmt == "json":
            return json_format.export_book(self)
        raise ValueError(f"Unsupported format: {fmt}")

    @property
    def json(self) -> str:
        return self.export("json")

    @json.setter
    def json(self, value: str) -> None:
        datasets = json_format.import_book(value)
        self._datasets = datasets
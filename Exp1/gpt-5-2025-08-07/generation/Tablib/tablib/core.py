import json
from typing import Iterable, List, Optional, Any


def _get_dataset_format_handlers(fmt: str):
    """Lazily import dataset format handlers."""
    if fmt == "csv":
        from .formats import _csv as mod
    elif fmt == "json":
        from .formats import _json as mod
    else:
        raise ValueError(f"Unsupported format: {fmt}")
    # expect mod has export_set, import_set
    return mod.export_set, mod.import_set


def _get_databook_format_handlers(fmt: str):
    """Lazily import databook format handlers."""
    if fmt == "json":
        from .formats import _json as mod
    else:
        raise ValueError(f"Unsupported format for databook: {fmt}")
    # expect mod has export_book, import_book
    return mod.export_book, mod.import_book


class Dataset:
    """A simple tabular data container."""

    def __init__(self, *rows, headers: Optional[Iterable[Any]] = None, title: Optional[str] = None):
        self._headers: Optional[List[Any]] = list(headers) if headers is not None else None
        self._data: List[List[Any]] = [list(r) for r in rows] if rows else []
        self.title: Optional[str] = title

    # ----- Shape helpers -----
    @property
    def height(self) -> int:
        return len(self._data)

    @property
    def width(self) -> int:
        if self._headers is not None:
            return len(self._headers)
        # else derive from data
        w = 0
        for r in self._data:
            if len(r) > w:
                w = len(r)
        return w

    # ----- Headers get/set -----
    @property
    def headers(self) -> Optional[List[Any]]:
        if self._headers is None:
            return None
        return list(self._headers)

    @headers.setter
    def headers(self, value: Optional[Iterable[Any]]) -> None:
        if value is None:
            self._headers = None
        else:
            self._headers = list(value)

    # ----- Row and column access -----
    def _row_as_width(self, row: List[Any]) -> List[Any]:
        """Return a list representing the row normalized to current width (pad/cut as needed)."""
        target_w = self.width
        if len(row) < target_w:
            return row + [None] * (target_w - len(row))
        elif len(row) > target_w:
            return row[:target_w]
        else:
            return list(row)

    def __getitem__(self, key):
        # slice access: return list of row tuples
        if isinstance(key, slice):
            rows = self._data[key]
            return [tuple(self._row_as_width(list(r))) for r in rows]
        # integer index: single row tuple
        if isinstance(key, int):
            row = self._data[key]
            return tuple(self._row_as_width(list(row)))
        # column access by header name
        if isinstance(key, str):
            if self._headers is None:
                raise KeyError("No headers defined for this dataset")
            try:
                idx = self._headers.index(key)
            except ValueError as e:
                raise KeyError(key) from e
            col: List[Any] = []
            for r in self._data:
                normalized = self._row_as_width(list(r))
                col.append(normalized[idx])
            return col
        raise TypeError("Invalid key type for Dataset")

    # ----- Mutation -----
    def append(self, row: Iterable[Any]) -> None:
        self._data.append(list(row))

    def append_col(self, values: Iterable[Any], header: Optional[Any] = None) -> None:
        vals = list(values)
        if self.height == 0:
            # Create rows from column values
            self._data = [[v] for v in vals]
        else:
            if len(vals) != self.height:
                raise ValueError("Column length must match dataset height")
            for i, v in enumerate(vals):
                self._data[i].append(v)

        # Manage headers to keep width aligned
        if self._headers is None:
            if header is not None:
                # build headers list to current width and set last to header
                # current width is len of first row
                w = self.width
                self._headers = [None] * w
                self._headers[-1] = header
        else:
            # headers exist, ensure we append a slot for new column
            # deduce whether we just expanded width by 1; append header or None
            # If headers length is equal to width-1 before this operation, extend. Otherwise, sync to width.
            if len(self._headers) < self.width:
                self._headers.append(header)
            else:
                # headers already at width; replace last?
                # Conservative: if header is not None and last header is None, set it
                if header is not None and self._headers[-1] is None:
                    self._headers[-1] = header

    # ----- Dict representation -----
    @property
    def dict(self) -> List[dict]:
        if self.height == 0:
            return []
        if self._headers is None:
            # fallback: use positional indices as keys
            w = self.width
            keys = list(range(w))
        else:
            keys = list(self._headers)
        out: List[dict] = []
        for r in self._data:
            row_norm = self._row_as_width(list(r))
            out.append({keys[i]: row_norm[i] for i in range(len(keys))})
        return out

    # ----- Serialization -----
    def export(self, fmt: str) -> str:
        exporter, _ = _get_dataset_format_handlers(fmt)
        return exporter(self)

    def _load_from_serialized(self, fmt: str, s: str) -> None:
        _, importer = _get_dataset_format_handlers(fmt)
        headers, rows = importer(s)
        self._headers = list(headers) if headers is not None else None
        self._data = [list(r) for r in rows]

    # CSV attribute
    @property
    def csv(self) -> str:
        return self.export("csv")

    @csv.setter
    def csv(self, s: str) -> None:
        self._load_from_serialized("csv", s)

    # JSON attribute
    @property
    def json(self) -> str:
        return self.export("json")

    @json.setter
    def json(self, s: str) -> None:
        # Determine if this is dataset-level JSON or book-level; here we assume dataset-level
        # Accept list of dicts or list of lists; otherwise error
        parsed = None
        try:
            parsed = json.loads(s)
        except Exception as e:
            raise ValueError("Invalid JSON for Dataset") from e
        # Re-serialize to pass through the centralized importer for uniform behavior
        if not isinstance(parsed, list):
            raise ValueError("JSON must represent a list for Dataset.json")
        self._load_from_serialized("json", s)


class Databook:
    """A collection of Datasets (sheets)."""

    def __init__(self, datasets: Iterable[Dataset]):
        self._datasets: List[Dataset] = list(datasets)

    @property
    def size(self) -> int:
        return len(self._datasets)

    def sheets(self) -> List[Dataset]:
        return list(self._datasets)

    def __iter__(self):
        return iter(self._datasets)

    def export(self, fmt: str) -> str:
        exporter, _ = _get_databook_format_handlers(fmt)
        return exporter(self)

    @property
    def json(self) -> str:
        return self.export("json")

    @json.setter
    def json(self, s: str) -> None:
        _, importer = _get_databook_format_handlers("json")
        try:
            spec = importer(s)
        except Exception as e:
            raise ValueError("Invalid JSON for Databook") from e
        # spec: list of sheets dicts with title, headers, data
        datasets: List[Dataset] = []
        for sh in spec:
            ds = Dataset(*[row for row in sh.get("data", [])], headers=sh.get("headers"))
            ds.title = sh.get("title")
            datasets.append(ds)
        self._datasets = datasets
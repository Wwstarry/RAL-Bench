from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Union, Any


Number = Union[int, float]


def _is_number(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


@dataclass
class Data:
    """
    Holds chart labels and numeric values.

    Normalization:
      - If values is 1D: [1,2,3] => [[1],[2],[3]]
      - If values is 2D: [[1,2],[3,4]] => same shape
    """

    labels: List[str]
    values: List[List[Number]]

    def __init__(self, labels: Optional[Sequence[str]] = None, values: Optional[Any] = None):
        self.labels = list(labels) if labels else []
        self.values = self._normalize_values(values)
        self._ensure_labels()
        self.validate()

    @classmethod
    def from_data(cls, labels: Sequence[str], values: Any) -> "Data":
        return cls(labels=labels, values=values)

    @property
    def n_rows(self) -> int:
        return len(self.values)

    @property
    def n_series(self) -> int:
        if not self.values:
            return 0
        return len(self.values[0])

    def _normalize_values(self, values: Any) -> List[List[Number]]:
        if values is None:
            return []

        # Accept sequences like list/tuple; reject strings/bytes.
        if isinstance(values, (str, bytes)):
            raise TypeError("values must be a sequence of numbers, not a string")

        # Determine 1D vs 2D: if the first element is a number => 1D.
        try:
            it = list(values)
        except TypeError:
            raise TypeError("values must be an iterable of numbers or iterables") from None

        if len(it) == 0:
            return []

        first = it[0]
        if _is_number(first):
            # 1D -> 2D per row
            out: List[List[Number]] = []
            for v in it:
                if not _is_number(v):
                    raise ValueError("non-numeric value found")
                out.append([v])
            return out

        # 2D
        out2: List[List[Number]] = []
        for row in it:
            try:
                row_list = list(row)
            except TypeError:
                raise TypeError("2D values must contain row iterables") from None
            if len(row_list) == 0:
                out2.append([])
                continue
            for v in row_list:
                if not _is_number(v):
                    raise ValueError("non-numeric value found")
            out2.append(row_list)
        return out2

    def _ensure_labels(self) -> None:
        # If no labels are provided, generate default 1..n.
        if not self.labels and self.values:
            self.labels = [str(i) for i in range(1, len(self.values) + 1)]

    def validate(self) -> None:
        # Labels length must match number of rows when labels are present.
        if self.labels and len(self.labels) != len(self.values):
            raise ValueError("labels length must match number of rows")

        # Rows must all have equal series length.
        if not self.values:
            return

        expected = len(self.values[0])
        for row in self.values:
            if len(row) != expected:
                raise ValueError("inconsistent number of series per row")

        # Must be numeric (already checked) but ensure castable to float for scaling.
        for row in self.values:
            for v in row:
                try:
                    float(v)
                except Exception as e:
                    raise ValueError("value is not numeric") from e
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence


def _is_number(x) -> bool:
    try:
        float(x)
        return True
    except Exception:
        return False


@dataclass
class Data:
    """
    Container for chart data.

    Attributes:
        labels: sequence of label strings (one per row)
        data: list of numeric series, where each series is a list of numbers
              aligned with labels (shape: [n_series][n_rows])
    """
    labels: List[str]
    data: List[List[float]]

    def __init__(
        self,
        labels: Optional[Sequence[str]] = None,
        data: Optional[Sequence[Sequence[float]]] = None,
    ):
        self.labels = list(labels) if labels is not None else []
        self.data = [list(map(float, s)) for s in (data or [])]
        self._validate()

    def _validate(self) -> None:
        if not self.data:
            return
        n = len(self.labels) if self.labels else len(self.data[0])
        for s in self.data:
            if len(s) != n:
                raise ValueError("All series must have the same length as labels")

        if self.labels and len(self.labels) != n:
            raise ValueError("labels length must match series length")

    @property
    def n_rows(self) -> int:
        if self.labels:
            return len(self.labels)
        if self.data:
            return len(self.data[0])
        return 0

    @property
    def n_series(self) -> int:
        return len(self.data)

    def values_for_row(self, idx: int) -> List[float]:
        return [series[idx] for series in self.data]

    def max_value(self) -> float:
        m = 0.0
        for s in self.data:
            for v in s:
                if v > m:
                    m = float(v)
        return m

    def max_value_per_series(self) -> List[float]:
        return [max(map(float, s)) if s else 0.0 for s in self.data]

    def sums_per_row(self) -> List[float]:
        sums = []
        for i in range(self.n_rows):
            sums.append(sum(self.values_for_row(i)))
        return sums

    @classmethod
    def from_dict(cls, mapping) -> "Data":
        """
        Convenience: accept {label: value} or {label: [v1,v2,...]}.
        """
        labels = []
        series = []
        if not mapping:
            return cls([], [])
        first = next(iter(mapping.values()))
        multi = isinstance(first, (list, tuple))
        if multi:
            k = len(first)
            series = [[] for _ in range(k)]
            for lab, vals in mapping.items():
                labels.append(str(lab))
                if len(vals) != k:
                    raise ValueError("All rows must have same number of values")
                for j in range(k):
                    if not _is_number(vals[j]):
                        raise ValueError("Non-numeric data")
                    series[j].append(float(vals[j]))
        else:
            series = [[]]
            for lab, v in mapping.items():
                labels.append(str(lab))
                if not _is_number(v):
                    raise ValueError("Non-numeric data")
                series[0].append(float(v))
        return cls(labels, series)
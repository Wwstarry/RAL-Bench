from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Tuple, Union


Number = Union[int, float]


def _is_number(x) -> bool:
    # Accept int/float and "number-like" objects (Decimal, numpy scalars) as long
    # as they can be converted to float.
    try:
        float(x)
        return True
    except Exception:
        return False


def _transpose(series_major: Sequence[Sequence[Number]]) -> List[List[Number]]:
    # series_major: n_series x n_rows -> row_major: n_rows x n_series
    if not series_major:
        return []
    n_rows = len(series_major[0])
    n_series = len(series_major)
    out: List[List[Number]] = []
    for i in range(n_rows):
        row = []
        for j in range(n_series):
            row.append(series_major[j][i])
        out.append(row)
    return out


@dataclass
class Data:
    """
    Holds chart data.

    labels: list of row labels (one per bar group / row)
    values: numeric data; accepted shapes:
      - row-major: len(values) == len(labels), each row has n_series numbers
      - series-major: len(values) == n_series, each series has len(labels) numbers
        (will be transposed to row-major internally)
    categories: optional list of series names
    """

    labels: List[str]
    values: List[List[Number]]
    categories: Optional[List[str]] = None

    def __init__(
        self,
        labels: Sequence[str],
        values: Sequence[Sequence[Number]],
        categories: Optional[Sequence[str]] = None,
    ):
        self.labels = list(labels)

        # Normalize values to list[list[number]] row-major.
        vals = [list(v) for v in values] if values is not None else []
        self.values = self._normalize_values(self.labels, vals)

        self.categories = list(categories) if categories is not None else None

        # Basic sanity for categories length (do not raise hard; keep permissive)
        if self.categories is not None and self.n_series and len(self.categories) != self.n_series:
            # Truncate or pad with generic names
            if len(self.categories) > self.n_series:
                self.categories = self.categories[: self.n_series]
            else:
                self.categories = self.categories + [f"series{idx+1}" for idx in range(len(self.categories), self.n_series)]

    @staticmethod
    def _normalize_values(labels: List[str], vals: List[List[Number]]) -> List[List[Number]]:
        if not labels:
            # With no labels, accept any vals but keep empty (no rows to draw).
            return []

        n_labels = len(labels)

        if vals == []:
            return [[] for _ in range(n_labels)]

        # Heuristic shape detection:
        # - If len(vals) == n_labels: assume row-major.
        # - Else if all series lengths match n_labels: assume series-major.
        if len(vals) == n_labels:
            row_major = vals
        else:
            if all(isinstance(s, (list, tuple)) and len(s) == n_labels for s in vals):
                row_major = _transpose(vals)
            else:
                raise ValueError(
                    "values shape not understood; expected row-major (len(values)==len(labels)) "
                    "or series-major (each series len == len(labels))"
                )

        # Validate rectangularity and numeric-like contents.
        # Determine n_series as max row length; then require all rows same length.
        n_series = 0
        for r in row_major:
            n_series = max(n_series, len(r))
        for idx, r in enumerate(row_major):
            if len(r) != n_series:
                raise ValueError("values must be rectangular (each row must have the same number of series)")
            for x in r:
                if not _is_number(x):
                    raise ValueError(f"non-numeric value at row {idx}: {x!r}")

        return row_major

    @property
    def n_rows(self) -> int:
        return len(self.labels)

    @property
    def n_series(self) -> int:
        if not self.values:
            return 0
        # values are normalized to rectangular, so length of first row is n_series
        return len(self.values[0]) if self.values[0] is not None else 0
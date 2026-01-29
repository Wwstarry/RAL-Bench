from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Union


Number = Union[int, float]


@dataclass
class Data:
    """
    Holds chart data:
      - labels: list[str]
      - series: list[list[number]]  (each inner list is one series across labels)

    This matches the common usage in termgraph-like APIs where the input is
    columns/series (not rows), and labels index the bars.
    """

    labels: List[str]
    series: List[List[Number]]

    def __init__(
        self,
        labels: Optional[Sequence[str]] = None,
        series: Optional[Sequence[Sequence[Number]]] = None,
    ):
        self.labels = list(labels) if labels is not None else []
        self.series = [list(s) for s in series] if series is not None else []

        # Normalize empty inputs
        if self.labels is None:
            self.labels = []
        if self.series is None:
            self.series = []

        # Basic validation/normalization: ensure rectangular where possible
        if self.series and self.labels:
            n = len(self.labels)
            for idx, s in enumerate(self.series):
                if len(s) != n:
                    raise ValueError(
                        f"Series {idx} has length {len(s)} but labels has length {n}"
                    )

    @property
    def n_rows(self) -> int:
        return len(self.labels)

    @property
    def n_series(self) -> int:
        return len(self.series)

    def get_row_values(self, row: int) -> List[Number]:
        """Return values across series for a given label row."""
        return [self.series[i][row] for i in range(self.n_series)]

    def iter_rows(self) -> Iterable[tuple[str, List[Number]]]:
        for i, lab in enumerate(self.labels):
            yield lab, self.get_row_values(i)
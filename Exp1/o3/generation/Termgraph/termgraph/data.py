"""
Extremely small data container used by the charts.  Only the attributes that
are required by the tests are present.
"""

from __future__ import annotations


class Data:
    """
    Holds *labels* and *series*.

    Parameters
    ----------
    labels:
        A list of strings, one per row/data-point.
    series:
        A list of *series*, each series itself being a list of numbers.
        The inner lists all need to be of identical length (== ``len(labels)``).
    """

    def __init__(self, labels, series):
        if not isinstance(labels, (list, tuple)):
            raise TypeError("labels must be a sequence")

        if not isinstance(series, (list, tuple)):
            raise TypeError("series must be a sequence of sequences")

        # Basic sanity ---------------------------------------------------------
        row_count = len(labels)
        for s in series:
            if len(s) != row_count:
                raise ValueError("every series must have the same length as labels")

        self.labels = list(labels)
        # Convert inner sequences to list so we may modify in place for
        # experiments/testing without harming the original data.
        self.series = [list(s) for s in series]

    # Reference implementation also exposes number of rows – handy.
    @property
    def rows(self) -> int:
        return len(self.labels)

    @property
    def cols(self) -> int:
        return len(self.series)

    # Quick constructor that matches the tests' preferred structure.
    @classmethod
    def from_rows(cls, rows):
        """
        Build a Data object from an *iterable* of rows where each row is
        ``(label, *values)``.  Primarily a convenience for test code.
        """
        labels = []
        # Transpose: we don't know number of series yet
        collected = []

        for row in rows:
            if not row:
                raise ValueError("row must not be empty")
            labels.append(row[0])
            values = row[1:]
            if not collected:
                collected = [[] for _ in values]
            if len(values) != len(collected):
                raise ValueError("inconsistent row length")
            for idx, v in enumerate(values):
                collected[idx].append(v)

        return cls(labels, collected)

    # Similar to Args – representation not required but helpful.
    def __repr__(self):  # pragma: no cover
        return f"{self.__class__.__name__}(labels={self.labels!r}, series={self.series!r})"
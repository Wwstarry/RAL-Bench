from typing import List, Sequence


class Data:
    """
    Helper container for charting data.

    labels: list of row labels (length N)
    series: list of rows, each row is a list of numbers (length N rows)
            Each row can contain 1..M series values for grouped/stacked charts.
    """

    def __init__(self, labels: Sequence[str], series: Sequence[Sequence[float]]):
        self.labels = list(labels)
        self.series = [list(row) for row in series]
        if len(self.labels) != len(self.series):
            raise ValueError("labels and series must have the same number of rows")
        # Normalize None rows
        for i, row in enumerate(self.series):
            if row is None:
                self.series[i] = []
        # Ensure numbers
        for i, row in enumerate(self.series):
            new_row = []
            for v in row:
                try:
                    if v is None:
                        new_row.append(0.0)
                    else:
                        new_row.append(float(v))
                except Exception:
                    raise ValueError(f"Non-numeric value at row {i}: {v}")
            self.series[i] = new_row

    def num_rows(self) -> int:
        return len(self.labels)

    def num_series(self) -> int:
        """Return the maximum number of series across rows."""
        m = 0
        for row in self.series:
            if len(row) > m:
                m = len(row)
        return m

    def max_value(self) -> float:
        """Maximum numeric value across all series values."""
        maxv = 0.0
        found = False
        for row in self.series:
            for v in row:
                if not found:
                    maxv = v
                    found = True
                else:
                    if v > maxv:
                        maxv = v
        return maxv if found else 0.0

    def max_per_series(self) -> List[float]:
        """
        Compute max per column series index across rows.
        Rows with missing columns are treated as 0.
        """
        count = self.num_series()
        maxs = [0.0] * count
        seen = [False] * count
        for row in self.series:
            for j in range(count):
                v = row[j] if j < len(row) else 0.0
                if not seen[j]:
                    maxs[j] = v
                    seen[j] = True
                else:
                    if v > maxs[j]:
                        maxs[j] = v
        # If some series never occurred, keep 0.0
        return maxs

    def sum_per_row(self) -> List[float]:
        return [sum(row) if row else 0.0 for row in self.series]

    def row(self, idx: int) -> List[float]:
        return self.series[idx]

    def label(self, idx: int) -> str:
        return self.labels[idx]
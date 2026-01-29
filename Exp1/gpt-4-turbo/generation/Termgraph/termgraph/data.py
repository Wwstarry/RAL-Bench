class Data:
    """
    Helper object for holding labels and numeric series.
    API-compatible with termgraph's Data.
    """
    def __init__(self, labels, data, colors=None):
        """
        labels: list of str
        data: list of list of numbers (each inner list is a series for a label)
        colors: optional list of color names or codes
        """
        self.labels = labels
        self.data = data
        self.colors = colors if colors is not None else []

    def __len__(self):
        return len(self.labels)

    def max_value(self):
        """Return the maximum value across all series."""
        return max(max(series) if series else 0 for series in self.data)

    def min_value(self):
        """Return the minimum value across all series."""
        return min(min(series) if series else 0 for series in self.data)

    def num_series(self):
        """Return the number of series per label."""
        return max(len(series) for series in self.data) if self.data else 0
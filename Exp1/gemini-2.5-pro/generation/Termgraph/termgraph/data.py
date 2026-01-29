# termgraph/data.py

class Data:
    """A container for chart data, including labels and numeric series."""

    def __init__(self, data, labels):
        """
        Initializes the Data object.

        Args:
            data (list of list of floats): The numeric data series.
                Example: [[10, 20, 30], [5, 15, 25]]
            labels (list of str): The labels for each data point.
                Example: ['A', 'B', 'C']
        """
        if not isinstance(data, list) or not all(isinstance(s, list) for s in data):
            raise TypeError("data must be a list of lists")
        if not isinstance(labels, list) or not all(isinstance(l, str) for l in labels):
            raise TypeError("labels must be a list of strings")

        num_points = len(labels)
        for s in data:
            if len(s) != num_points:
                raise ValueError("All data series must have the same length as the labels list.")

        self.series = data
        self.labels = labels

    @property
    def num_series(self):
        """Returns the number of data series."""
        return len(self.series)

    @property
    def num_points(self):
        """Returns the number of data points (labels)."""
        return len(self.labels)
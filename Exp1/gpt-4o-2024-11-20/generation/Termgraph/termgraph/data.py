# termgraph/data.py

class Data:
    """
    A helper object for holding labels and numeric series.
    """
    def __init__(self, labels, series):
        """
        Initialize the Data object.

        :param labels: List of labels for the data.
        :param series: List of numeric series (list of lists).
        """
        self.labels = labels
        self.series = series

    def validate(self):
        """
        Validate the data to ensure labels and series are consistent.
        """
        if len(self.labels) != len(self.series):
            raise ValueError("Labels and series length mismatch.")
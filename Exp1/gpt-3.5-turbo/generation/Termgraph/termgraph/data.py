class Data:
    def __init__(self, labels=None, data=None):
        """
        labels: list of strings
        data: list of lists of numbers (each inner list is a series)
        """
        self.labels = labels or []
        self.data = data or []

    def max_value(self):
        max_val = None
        for series in self.data:
            for val in series:
                if max_val is None or val > max_val:
                    max_val = val
        return max_val if max_val is not None else 0

    def min_value(self):
        min_val = None
        for series in self.data:
            for val in series:
                if min_val is None or val < min_val:
                    min_val = val
        return min_val if min_val is not None else 0

    def num_items(self):
        if self.data:
            return len(self.data[0])
        return 0

    def num_series(self):
        return len(self.data)
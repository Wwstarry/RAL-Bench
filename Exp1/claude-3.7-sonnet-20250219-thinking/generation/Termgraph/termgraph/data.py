class Data:
    """
    Helper class to hold data for charts.
    """
    def __init__(self, labels=None, data=None):
        """
        Initialize a Data object.
        
        Args:
            labels: List of labels for data series
            data: List of numeric data series
        """
        self.labels = labels or []
        self.data = data or []
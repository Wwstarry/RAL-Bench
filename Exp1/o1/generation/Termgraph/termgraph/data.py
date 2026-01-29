class Data:
    """
    Data object that holds labels and numeric data series for charting.
    
    Attributes:
        labels (list of str): Labels corresponding to each data row/series.
        data (list of list of float): Numeric data; each inner list represents a series.
    """
    def __init__(self, labels=None, data=None):
        self.labels = labels or []
        self.data = data or []
"""
Data container for termgraph charts.
"""


class Data:
    """
    Container for chart data with labels and numeric series.
    
    Attributes:
        labels: List of labels for each row.
        series: List of lists, where each inner list is a numeric series.
    """
    
    def __init__(self, labels=None, series=None):
        """
        Initialize Data object.
        
        Args:
            labels: List of string labels for rows.
            series: List of lists of numeric values.
        """
        self.labels = labels or []
        self.series = series or []
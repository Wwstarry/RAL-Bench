"""
Data container for termgraph charts
"""


class Data:
    """
    Container for chart data with labels and numeric series.
    """
    
    def __init__(self, labels=None, data=None):
        """
        Initialize Data container.
        
        Args:
            labels: List of string labels for each data row
            data: List of numeric values or lists of numeric values for each row
        """
        self.labels = labels if labels is not None else []
        self.data = data if data is not None else []
    
    def __len__(self):
        """Return the number of data rows."""
        return len(self.data)
    
    def __iter__(self):
        """Iterate over (label, values) pairs."""
        for i in range(len(self)):
            label = self.labels[i] if i < len(self.labels) else ""
            values = self.data[i]
            yield (label, values)
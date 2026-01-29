"""
Data structures for holding chart data.
"""

from typing import List, Union, Optional


class Data:
    """
    Container for chart data with labels and numeric series.
    """
    
    def __init__(self, labels: List[str], data: List[List[Union[int, float]]]):
        """
        Initialize Data object.
        
        Args:
            labels: List of label strings
            data: List of data series, each series is a list of numeric values
        """
        self.labels = labels
        self.data = data
        
        # Validate data dimensions
        if len(data) > 0:
            series_length = len(data[0])
            for series in data:
                if len(series) != series_length:
                    raise ValueError("All data series must have the same length")
                if len(series) != len(labels):
                    raise ValueError("Number of data points must match number of labels")
    
    @property
    def num_labels(self) -> int:
        """Return number of labels."""
        return len(self.labels)
    
    @property
    def num_series(self) -> int:
        """Return number of data series."""
        return len(self.data)
    
    def get_max_value(self, series_idx: Optional[int] = None) -> Union[int, float]:
        """
        Get maximum value across all series or in a specific series.
        
        Args:
            series_idx: Optional index of specific series, None for all series
            
        Returns:
            Maximum value
        """
        if series_idx is not None:
            return max(self.data[series_idx])
        
        max_val = float('-inf')
        for series in self.data:
            series_max = max(series)
            if series_max > max_val:
                max_val = series_max
        return max_val
    
    def get_min_value(self, series_idx: Optional[int] = None) -> Union[int, float]:
        """
        Get minimum value across all series or in a specific series.
        
        Args:
            series_idx: Optional index of specific series, None for all series
            
        Returns:
            Minimum value
        """
        if series_idx is not None:
            return min(self.data[series_idx])
        
        min_val = float('inf')
        for series in self.data:
            series_min = min(series)
            if series_min < min_val:
                min_val = series_min
        return min_val
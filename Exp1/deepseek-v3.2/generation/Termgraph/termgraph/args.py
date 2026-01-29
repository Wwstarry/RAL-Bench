"""
Command-line arguments and rendering options.
"""

from typing import List, Optional


class Args:
    """
    Container for chart rendering options.
    """
    
    def __init__(
        self,
        width: int = 50,
        stacked: bool = False,
        different_scale: bool = False,
        no_labels: bool = False,
        format: str = "{:>5.2f}",
        suffix: str = "",
        vertical: bool = False,
        histogram: bool = False,
        no_values: bool = False,
        color: Optional[List[str]] = None,
        labels: Optional[List[str]] = None,
        title: Optional[str] = None,
        **kwargs  # Accept additional arguments for compatibility
    ):
        """
        Initialize Args object with rendering options.
        
        Args:
            width: Chart width in characters
            stacked: Whether to stack bars
            different_scale: Use different scales for each series
            no_labels: Hide labels
            format: Format string for numeric values
            suffix: Suffix to append to values
            vertical: Use vertical orientation
            histogram: Render as histogram
            no_values: Hide numeric values
            color: List of colors for each series
            labels: Custom labels (overrides data labels)
            title: Chart title
            **kwargs: Additional arguments for compatibility
        """
        self.width = width
        self.stacked = stacked
        self.different_scale = different_scale
        self.no_labels = no_labels
        self.format = format
        self.suffix = suffix
        self.vertical = vertical
        self.histogram = histogram
        self.no_values = no_values
        self.color = color or []
        self.labels = labels
        self.title = title
        
        # Store any additional arguments
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    @classmethod
    def from_dict(cls, config: dict) -> 'Args':
        """
        Create Args instance from dictionary.
        
        Args:
            config: Dictionary of configuration options
            
        Returns:
            Args instance
        """
        return cls(**config)
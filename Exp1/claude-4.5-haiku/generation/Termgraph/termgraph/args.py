"""
Arguments container for termgraph chart rendering options.
"""


class Args:
    """
    Container for chart rendering options.
    
    Attributes:
        width: Width of the chart in characters.
        stacked: Whether to render stacked bars.
        different_scale: Whether each series has its own scale.
        no_labels: Whether to hide row labels.
        format: Format string for numeric values (e.g., "{:.2f}").
        suffix: Suffix to append to numeric values.
        vertical: Whether to render vertically (not implemented).
        histogram: Whether to render as histogram (not implemented).
        no_values: Whether to hide numeric values.
        color: List of colors for series (not implemented).
        labels: List of labels for series.
        title: Title for the chart.
    """
    
    def __init__(
        self,
        width=50,
        stacked=False,
        different_scale=False,
        no_labels=False,
        format="{:.0f}",
        suffix="",
        vertical=False,
        histogram=False,
        no_values=False,
        color=None,
        labels=None,
        title=None,
    ):
        """
        Initialize Args object with rendering options.
        
        Args:
            width: Width of the chart in characters.
            stacked: Whether to render stacked bars.
            different_scale: Whether each series has its own scale.
            no_labels: Whether to hide row labels.
            format: Format string for numeric values.
            suffix: Suffix to append to numeric values.
            vertical: Whether to render vertically.
            histogram: Whether to render as histogram.
            no_values: Whether to hide numeric values.
            color: List of colors for series.
            labels: List of labels for series.
            title: Title for the chart.
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
        self.labels = labels or []
        self.title = title
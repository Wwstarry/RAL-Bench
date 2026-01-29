"""
Arguments container for termgraph rendering options
"""


class Args:
    """
    Container for chart rendering arguments and options.
    """
    
    def __init__(self, 
                 width=50,
                 stacked=False,
                 different_scale=False,
                 no_labels=False,
                 format="{:.2f}",
                 suffix="",
                 vertical=False,
                 histogram=False,
                 no_values=False,
                 color=None,
                 labels=True,
                 title=None):
        """
        Initialize Args container.
        
        Args:
            width: Width of the chart in characters (default: 50)
            stacked: Whether to render as stacked chart (default: False)
            different_scale: Use different scales for each series (default: False)
            no_labels: Don't show labels (default: False)
            format: Format string for numeric values (default: "{:.2f}")
            suffix: Suffix to append to values (default: "")
            vertical: Render chart vertically (default: False)
            histogram: Render as histogram (default: False)
            no_values: Don't show numeric values (default: False)
            color: Color configuration (default: None)
            labels: Show labels (default: True)
            title: Chart title (default: None)
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
        self.color = color
        self.labels = labels
        self.title = title
class Args:
    """
    Helper class to encapsulate rendering options.
    """
    def __init__(self, 
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
                 title=""):
        """
        Initialize an Args object with rendering options.
        
        Args:
            width: Width of the chart
            stacked: Whether the chart is stacked
            different_scale: Use different scale for each data series
            no_labels: Hide labels
            format: Format string for values
            suffix: Suffix to append to values
            vertical: Use vertical orientation
            histogram: Display as histogram
            no_values: Hide values
            color: Color for the chart
            labels: Custom labels
            title: Chart title
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
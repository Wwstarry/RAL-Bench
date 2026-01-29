class Args:
    def __init__(self,
                 width=50,
                 stacked=False,
                 different_scale=False,
                 no_labels=False,
                 format='{:<5.2f}',
                 suffix='',
                 vertical=False,
                 histogram=False,
                 no_values=False,
                 color=None,
                 labels=None,
                 title=None):
        """
        width: int - max width of chart bars
        stacked: bool - render stacked bar chart
        different_scale: bool - use different scale per series (not implemented)
        no_labels: bool - suppress labels on left
        format: str - format string for numeric values
        suffix: str - suffix to append to values
        vertical: bool - vertical bars (not implemented)
        histogram: bool - histogram mode (not implemented)
        no_values: bool - suppress numeric values on bars
        color: list or None - colors per series (not implemented)
        labels: list or None - override labels
        title: str or None - chart title
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
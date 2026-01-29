# termgraph/args.py

class Args:
    """
    A helper object encapsulating rendering options.
    """
    def __init__(self, width=50, stacked=False, different_scale=False, no_labels=False,
                 format="{:.2f}", suffix="", vertical=False, histogram=False,
                 no_values=False, color=False, labels=None, title=None):
        """
        Initialize the Args object.

        :param width: Width of the chart.
        :param stacked: Whether to render stacked bar charts.
        :param different_scale: Use different scales for series.
        :param no_labels: Hide labels.
        :param format: Format string for numeric values.
        :param suffix: Suffix for numeric values.
        :param vertical: Render vertical charts.
        :param histogram: Render histogram charts.
        :param no_values: Hide numeric values.
        :param color: Use colors in the chart.
        :param labels: Custom labels for the chart.
        :param title: Title of the chart.
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
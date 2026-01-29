class Args:
    """
    Args object encapsulating rendering options for charts.

    Attributes:
        width (int): Maximum width of the bar.
        stacked (bool): Whether bars are stacked.
        different_scale (bool): Each row uses its own scale if True.
        no_labels (bool): Whether to print labels.
        format (str): Format string for numeric values (e.g. "%.2f").
        suffix (str): Suffix to append to numeric values (e.g. "%").
        vertical (bool): Whether to render vertical bars (NOT fully implemented).
        histogram (bool): Whether to interpret data in a histogramlike way (NOT fully implemented).
        no_values (bool): Whether to hide numeric values in output.
        color (bool): Whether to apply color to bars.
        labels (list of str): Override labels if not None.
        title (str): Title to print before chart.
    """
    def __init__(
        self,
        width=50,
        stacked=False,
        different_scale=False,
        no_labels=False,
        fmt="%.2f",
        suffix="",
        vertical=False,
        histogram=False,
        no_values=False,
        color=False,
        labels=None,
        title=None,
    ):
        self.width = width
        self.stacked = stacked
        self.different_scale = different_scale
        self.no_labels = no_labels
        self.format = fmt
        self.suffix = suffix
        self.vertical = vertical
        self.histogram = histogram
        self.no_values = no_values
        self.color = color
        self.labels = labels
        self.title = title
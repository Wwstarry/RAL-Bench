class Args:
    """
    Helper object encapsulating rendering options.
    """
    def __init__(
        self,
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
        labels=None,
        title=None
    ):
        self.width = width
        self.stacked = stacked
        self.different_scale = different_scale
        self.no_labels = no_labels
        self.format = format
        self.suffix = suffix
        self.vertical = vertical
        self.histogram = histogram
        self.no_values = no_values
        self.color = color if color is not None else []
        self.labels = labels if labels is not None else []
        self.title = title
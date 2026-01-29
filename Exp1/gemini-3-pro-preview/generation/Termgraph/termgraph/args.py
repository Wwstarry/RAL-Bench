class Args:
    def __init__(self, width=50, format="{:<5.2f}", suffix="", no_labels=False,
                 no_values=False, color=None, vertical=False, stacked=False,
                 different_scale=False, histogram=False, title=None):
        """
        Encapsulates rendering options for the chart.
        """
        self.width = width
        self.format = format
        self.suffix = suffix
        self.no_labels = no_labels
        self.no_values = no_values
        self.color = color
        self.vertical = vertical
        self.stacked = stacked
        self.different_scale = different_scale
        self.histogram = histogram
        self.title = title
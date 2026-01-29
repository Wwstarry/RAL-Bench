class Args:
    def __init__(self, width=50, stacked=False, different_scale=False,
                 no_labels=False, format="{:>5.2f}", suffix="", vertical=False,
                 histogram=False, no_values=False, color=None, labels=None, title=""):
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
# termgraph/args.py

class Args:
    """A simple container for chart rendering arguments."""
    __slots__ = (
        'width', 'stacked', 'different_scale', 'no_labels', 'format',
        'suffix', 'vertical', 'histogram', 'no_values', 'color',
        'labels', 'title'
    )

    def __init__(self, **kwargs):
        # Set default values based on common usage
        self.width: int = 50
        self.stacked: bool = False
        self.different_scale: bool = False
        self.no_labels: bool = False
        self.format: str = '{:<5.2f}'
        self.suffix: str = ''
        self.vertical: bool = False
        self.histogram: bool = False
        self.no_values: bool = False
        self.color = None  # Can be a list of color names or codes
        self.labels = None # Usually derived from Data, kept for compatibility
        self.title: str = None

        # Override defaults with any provided kwargs
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
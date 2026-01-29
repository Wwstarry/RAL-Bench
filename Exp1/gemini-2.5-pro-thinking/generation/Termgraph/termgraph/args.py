class Args:
    """Helper class to hold and manage charting arguments."""

    def __init__(self, **kwargs):
        """
        Initializes the Args object, setting defaults for any arguments
        not provided in kwargs.
        """
        defaults = {
            'width': 50,
            'stacked': False,
            'different_scale': False,
            'no_labels': False,
            'format': '{:<5.2f}',
            'suffix': '',
            'vertical': False,
            'histogram': False,
            'no_values': False,
            'color': None,
            'labels': None,
            'title': None,
        }
        # Overwrite defaults with any provided kwargs
        defaults.update(kwargs)
        for key, value in defaults.items():
            setattr(self, key, value)
class Data:
    """Helper class to hold data series and labels for charting."""

    def __init__(self, data, labels):
        """
        Initializes the Data object.

        Args:
            data (list of lists of float): The numeric data series. Each inner
                                           list corresponds to a label.
            labels (list of str): The labels for each data series.
        """
        self.data = data
        self.labels = labels
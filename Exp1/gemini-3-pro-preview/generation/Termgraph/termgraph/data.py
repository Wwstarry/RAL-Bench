class Data:
    def __init__(self, data, labels):
        """
        Holds the data and labels for the chart.
        
        :param data: A list of lists containing numeric values. 
                     Example: [[10], [20]] for simple bars, 
                     [[10, 5], [20, 3]] for stacked/multi-series.
        :param labels: A list of strings corresponding to the rows in data.
        """
        self.data = data
        self.labels = labels
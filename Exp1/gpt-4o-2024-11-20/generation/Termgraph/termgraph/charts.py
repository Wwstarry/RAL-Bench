# termgraph/charts.py

class BarChart:
    """
    A class for rendering horizontal bar charts.
    """
    def __init__(self, data, args):
        """
        Initialize the BarChart object.

        :param data: Data object containing labels and series.
        :param args: Args object containing rendering options.
        """
        self.data = data
        self.args = args

    def draw(self):
        """
        Render the horizontal bar chart to stdout.
        """
        self.data.validate()
        max_value = max(max(series) for series in self.data.series)
        scale = self.args.width / max_value if max_value > 0 else 1

        for label, series in zip(self.data.labels, self.data.series):
            if not self.args.no_labels:
                print(f"{label}: ", end="")
            for value in series:
                bar = "#" * int(value * scale)
                print(bar, end=" ")
                if not self.args.no_values:
                    print(f"({self.args.format.format(value)}{self.args.suffix})", end=" ")
            print()


class StackedChart:
    """
    A class for rendering stacked bar charts.
    """
    def __init__(self, data, args):
        """
        Initialize the StackedChart object.

        :param data: Data object containing labels and series.
        :param args: Args object containing rendering options.
        """
        self.data = data
        self.args = args

    def draw(self):
        """
        Render the stacked bar chart to stdout.
        """
        self.data.validate()
        max_value = max(sum(series) for series in self.data.series)
        scale = self.args.width / max_value if max_value > 0 else 1

        for label, series in zip(self.data.labels, self.data.series):
            if not self.args.no_labels:
                print(f"{label}: ", end="")
            cumulative = 0
            for value in series:
                cumulative += value
                bar = "#" * int(cumulative * scale)
                print(bar, end=" ")
                if not self.args.no_values:
                    print(f"({self.args.format.format(cumulative)}{self.args.suffix})", end=" ")
            print()
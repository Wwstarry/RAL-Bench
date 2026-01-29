import sys

# ANSI color codes
COLORS = {
    'red': '\033[91m',
    'green': '\033[92m',
    'blue': '\033[94m',
    'yellow': '\033[93m',
    'magenta': '\033[95m',
    'cyan': '\033[96m',
    'reset': '\033[0m'
}
TICK = '█'

class BarChart:
    """A horizontal bar chart."""

    def __init__(self, data, args):
        """
        Initializes a BarChart.

        Args:
            data (Data): A Data object containing labels and series.
            args (Args): An Args object containing rendering options.
        """
        self.data_obj = data
        self.args = args

    def _get_max_label_width(self):
        """Calculates the width of the longest label."""
        if self.args.no_labels or not self.data_obj.labels:
            return 0
        return max(len(label) for label in self.data_obj.labels)

    def _get_max_value(self):
        """Finds the maximum value across all data points."""
        if not self.data_obj.data:
            return 0
        all_values = [item for sublist in self.data_obj.data for item in sublist]
        return max(all_values) if all_values else 0

    def draw(self):
        """Renders the bar chart to standard output."""
        if self.args.title:
            print(self.args.title)

        max_val = self._get_max_value()
        if max_val == 0:
            max_val = 1  # Avoid division by zero

        label_width = self._get_max_label_width()

        # Estimate width needed for the value string
        value_width = 0
        if not self.args.no_values:
            formatted_max_val = self.args.format.format(max_val) + self.args.suffix
            value_width = len(formatted_max_val)

        # Calculate available width for the bar itself
        other_elements_width = 0
        if not self.args.no_labels:
            other_elements_width += label_width + 1  # label + space
        if not self.args.no_values:
            other_elements_width += value_width + 1  # space + value

        bar_width = self.args.width - other_elements_width
        if bar_width < 1:
            bar_width = 1

        scale = bar_width / max_val

        for i, label in enumerate(self.data_obj.labels):
            if not self.data_obj.data[i]:
                continue
            value = self.data_obj.data[i][0]  # Bar chart has one value per label

            # Prepare label part
            label_str = ""
            if not self.args.no_labels:
                label_str = f"{label:<{label_width}} "

            # Prepare bar part
            bar_len = int(value * scale)
            bar_str = TICK * bar_len

            # Apply color if specified
            if self.args.color:
                color_name = self.args.color[0] if isinstance(self.args.color, list) else self.args.color
                color_code = COLORS.get(color_name, '')
                if color_code:
                    bar_str = f"{color_code}{bar_str}{COLORS['reset']}"

            # Prepare value part
            value_str = ""
            if not self.args.no_values:
                formatted_value = self.args.format.format(value) + self.args.suffix
                value_str = f" {formatted_value}"

            print(f"{label_str}{bar_str}{value_str}")


class StackedChart(BarChart):
    """A horizontal stacked bar chart."""

    def __init__(self, data, args):
        super().__init__(data, args)
        # Set up colors to cycle through for stacks
        available_colors = list(COLORS.keys())
        available_colors.remove('reset')
        self.colors = self.args.color or available_colors

    def _get_max_value(self):
        """For stacked charts, the max value is the max of the sum of each row."""
        if not self.data_obj.data:
            return 0
        row_sums = [sum(row) for row in self.data_obj.data]
        return max(row_sums) if row_sums else 0

    def draw(self):
        """Renders the stacked bar chart to standard output."""
        if self.args.title:
            print(self.args.title)

        max_total = self._get_max_value()
        if max_total == 0:
            max_total = 1

        label_width = self._get_max_label_width()

        # Estimate value width based on the max total
        value_width = 0
        if not self.args.no_values:
            formatted_max_val = self.args.format.format(max_total) + self.args.suffix
            value_width = len(formatted_max_val)

        other_elements_width = 0
        if not self.args.no_labels:
            other_elements_width += label_width + 1
        if not self.args.no_values:
            other_elements_width += value_width + 1

        bar_width = self.args.width - other_elements_width
        if bar_width < 1:
            bar_width = 1

        scale = bar_width / max_total

        for i, label in enumerate(self.data_obj.labels):
            row_data = self.data_obj.data[i]
            row_total = sum(row_data)

            # Prepare label part
            label_str = ""
            if not self.args.no_labels:
                label_str = f"{label:<{label_width}} "

            # Prepare bar part by building segments
            bar_str = ""
            cumulative_len = 0
            for j, value in enumerate(row_data):
                # Calculate target end position to avoid rounding errors
                target_cumulative_len = round(sum(row_data[:j + 1]) * scale)
                segment_len = target_cumulative_len - cumulative_len

                if segment_len > 0:
                    color_name = self.colors[j % len(self.colors)]
                    color_code = COLORS.get(color_name, '')
                    bar_str += f"{color_code}{TICK * segment_len}"

                cumulative_len = target_cumulative_len

            if bar_str:
                bar_str += COLORS['reset']

            # Prepare value part
            value_str = ""
            if not self.args.no_values:
                formatted_value = self.args.format.format(row_total) + self.args.suffix
                value_str = f" {formatted_value}"

            print(f"{label_str}{bar_str}{value_str}")
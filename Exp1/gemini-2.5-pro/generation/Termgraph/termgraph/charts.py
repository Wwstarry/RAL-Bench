# termgraph/charts.py

import re

# ANSI color codes
COLORS = [94, 92, 93, 96, 95, 91, 90]  # blue, green, yellow, cyan, magenta, red, black
TICK = '█'
COLOR_MAP = {
    'red': 91, 'green': 92, 'yellow': 93, 'blue': 94,
    'magenta': 95, 'cyan': 96, 'white': 97, 'black': 90,
}

def _color(text, color_code):
    """Applies ANSI color to text."""
    if color_code is None:
        return text
    return f"\033[{color_code}m{text}\033[0m"

def _len_no_ansi(text):
    """Calculates the visible length of a string, ignoring ANSI codes."""
    return len(re.sub(r'\033\[[0-9;]*m', '', text))

def _get_color_code(color_input, index):
    """Determines the color code to use based on input and index."""
    if color_input is None:
        return COLORS[index % len(COLORS)]
    
    if isinstance(color_input, list) and color_input:
        color = color_input[index % len(color_input)]
        if isinstance(color, str):
            return COLOR_MAP.get(color.lower(), COLORS[index % len(COLORS)])
        elif isinstance(color, int):
            return color
    
    return COLORS[index % len(COLORS)]

class BarChart:
    """A horizontal bar chart."""

    def __init__(self, data, args):
        self.data = data
        self.args = args

    def draw(self):
        """Renders the bar chart to stdout."""
        if self.args.title:
            print(self.args.title)

        if not self.data.series or not self.data.series[0]:
            return

        max_label_width = 0
        if not self.args.no_labels and self.data.labels:
            max_label_width = max(len(label) for label in self.data.labels)

        all_values = [val for series in self.data.series for val in series if val is not None]
        max_val = max(all_values) if all_values else 0
        
        max_value_width = 0
        if not self.args.no_values:
            max_value_width = len(self.args.format.format(max_val) + self.args.suffix)

        if self.args.different_scale:
            max_series_vals = [max(s) if s else 0 for s in self.data.series]
        else:
            max_series_vals = [max_val] * self.data.num_series

        rows = list(zip(*self.data.series))

        for i, label in enumerate(self.data.labels):
            row_values = rows[i]
            
            for j, value in enumerate(row_values):
                if j == 0:
                    if not self.args.no_labels:
                        print(f"{label:<{max_label_width}} |", end='')
                    else:
                        print(" ", end='')
                else:
                    if not self.args.no_labels:
                        print(f"{'':<{max_label_width}} |", end='')
                    else:
                        print(" ", end='')

                max_current_val = max_series_vals[j]
                
                label_part_width = max_label_width + 3 if not self.args.no_labels else 1
                value_part_width = max_value_width + 1 if not self.args.no_values else 0
                bar_width = self.args.width - label_part_width - value_part_width
                if bar_width < 0: bar_width = 0

                bar_len = int(value / max_current_val * bar_width) if max_current_val > 0 else 0
                
                bar_str = TICK * bar_len
                if self.args.color:
                    color_code = _get_color_code(self.args.color, j)
                    bar_str = _color(bar_str, color_code)
                
                print(bar_str, end='')
                
                if not self.args.no_values:
                    print(f"{'':<{bar_width - bar_len}}", end='')
                    value_str = self.args.format.format(value) + self.args.suffix
                    print(f" {value_str}", end='')
                
                print()

class StackedChart(BarChart):
    """A stacked horizontal bar chart."""

    def draw(self):
        """Renders the stacked bar chart to stdout."""
        if self.args.title:
            print(self.args.title)

        if not self.data.series or not self.data.series[0]:
            return

        max_label_width = 0
        if not self.args.no_labels and self.data.labels:
            max_label_width = max(len(label) for label in self.data.labels)

        rows = list(zip(*self.data.series))
        row_totals = [sum(row) for row in rows]
        max_total = max(row_totals) if row_totals else 0
        
        max_value_width = 0
        if not self.args.no_values:
            max_value_width = len(self.args.format.format(max_total) + self.args.suffix)

        for i, label in enumerate(self.data.labels):
            if not self.args.no_labels:
                print(f"{label:<{max_label_width}} |", end='')
            else:
                print(" ", end='')

            row_values = rows[i]
            row_total = row_totals[i]
            
            label_part_width = max_label_width + 3 if not self.args.no_labels else 1
            value_part_width = max_value_width + 1 if not self.args.no_values else 0
            bar_width = self.args.width - label_part_width - value_part_width
            if bar_width < 0: bar_width = 0

            bar_str = ""
            total_len = 0
            
            if max_total > 0:
                for j, value in enumerate(row_values):
                    cumulative_len = int(sum(row_values[:j+1]) / max_total * bar_width)
                    segment_len = cumulative_len - total_len
                    total_len = cumulative_len
                    
                    segment_str = TICK * segment_len
                    if self.args.color:
                        color_code = _get_color_code(self.args.color, j)
                        segment_str = _color(segment_str, color_code)
                    
                    bar_str += segment_str
            
            print(bar_str, end='')
            
            if not self.args.no_values:
                pad_len = bar_width - _len_no_ansi(bar_str)
                print(f"{'':<{pad_len}}", end='')
                value_str = self.args.format.format(row_total) + self.args.suffix
                print(f" {value_str}", end='')
            
            print()
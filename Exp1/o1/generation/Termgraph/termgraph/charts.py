import sys

# Simple ANSI colors to demonstrate color usage if enabled.
# You can customize if needed.
COLORS = [
    "\033[90m",  # Dark Gray
    "\033[91m",  # Red
    "\033[92m",  # Green
    "\033[93m",  # Yellow
    "\033[94m",  # Blue
    "\033[95m",  # Magenta
    "\033[96m",  # Cyan
    "\033[0m",   # Reset
]

def _scaled_value(series, args):
    """
    Compute scaled lengths for each numeric value in 'series' based on the Args configuration.
    Returns a list of (scaled_value, original_value).
    """
    # If there are no data points, return early.
    if not series:
        return []

    max_val = max(series)
    if max_val == 0:
        return [(0, val) for val in series]

    # The scale factor depends on whether we have a specified width.
    scale = max_val / float(args.width) if args.width else 1.0
    scaled = []
    for val in series:
        length = int(round(val / scale)) if scale else 0
        scaled.append((length, val))
    return scaled


class BarChart:
    """
    BarChart renders horizontal bar charts using Data and Args.
    """
    def __init__(self, data, args):
        """
        data: instance of Data
        args: instance of Args
        """
        self.data = data
        self.args = args

    def draw(self):
        """
        Render the bar chart to stdout.
        """
        if self.args.title:
            print(self.args.title)

        # Possibly override labels if provided in args
        labels = self.args.labels if self.args.labels else self.data.labels
        series_list = self.data.data  # each element is a list (in case of multi-series, but for BarChart we handle row by row)

        for i, series in enumerate(series_list):
            # If we need different scales for each row, we compute them separately.
            # Otherwise, we compute a single scaling factor from all data combined.
            if self.args.different_scale:
                scaled_vals = _scaled_value(series, self.args)
            else:
                # Collect all series from all rows in one flatten list to figure out single scale
                all_data = [val for row_data in series_list for val in row_data]
                max_val = max(all_data) if all_data else 0
                # We'll scale with respect to the global max.
                scale = max_val / float(self.args.width) if (max_val and self.args.width) else 1.0
                scaled_vals = []
                for val in series:
                    length = int(round(val / scale)) if scale else 0
                    scaled_vals.append((length, val))

            # Print label if not suppressed
            label_text = labels[i] if i < len(labels) else f"row_{i}"
            if not self.args.no_labels:
                print(f"{label_text}:")
            
            # For each value in this row, print a separate bar
            for s_len, s_val in scaled_vals:
                bar_str = "#" * s_len
                # Apply color?
                if self.args.color:
                    color_code = COLORS[(i % (len(COLORS) - 1))]  # last is reset
                    bar_str = f"{color_code}{bar_str}{COLORS[-1]}"

                # Optionally show numeric values at the end
                display_val = ""
                if not self.args.no_values:
                    formatted_val = self.args.format % s_val
                    display_val = f"  {formatted_val}{self.args.suffix}"

                print(f"{bar_str}{display_val}")

            # Blank line after each row
            print()
        

class StackedChart:
    """
    StackedChart renders stacked horizontal bar charts using Data and Args.
    Each row in Data.data is treated as a set of values that should be stacked
    on the same line.
    """
    def __init__(self, data, args):
        """
        data: instance of Data
        args: instance of Args
        """
        self.data = data
        self.args = args

    def draw(self):
        """
        Render the stacked bar chart to stdout.
        """
        if self.args.title:
            print(self.args.title)

        # Possibly override labels if provided in args
        labels = self.args.labels if self.args.labels else self.data.labels
        # self.data.data is a list of lists, each "row" is a set of values to be stacked horizontally

        # Flatten all data if not different scale
        if not self.args.different_scale:
            all_data = [val for row in self.data.data for val in row]
            max_val = max(all_data) if all_data else 0
            global_scale = max_val / float(self.args.width) if (max_val and self.args.width) else 1.0
        else:
            global_scale = None

        for i, row in enumerate(self.data.data):
            if not self.args.no_labels:
                label_text = labels[i] if i < len(labels) else f"row_{i}"
                print(f"{label_text}:")

            if self.args.different_scale:
                scaled_vals = _scaled_value(row, self.args)
            else:
                scaled_vals = []
                for val in row:
                    length = int(round(val / global_scale)) if global_scale else 0
                    scaled_vals.append((length, val))

            # Build stacked bar on one line
            line_parts = []
            for idx, (s_len, s_val) in enumerate(scaled_vals):
                part_str = "#" * s_len
                # Apply color?
                if self.args.color:
                    color_code = COLORS[(idx % (len(COLORS) - 1))]
                    part_str = f"{color_code}{part_str}{COLORS[-1]}"
                line_parts.append(part_str)

            stacked_line = "".join(line_parts)
            # Combine numeric values if not suppressed
            if not self.args.no_values:
                # Summaries or each value?
                # We'll just show the sum at the end of the line, or each value?
                # For compatibility, let's just do the sum if multiple values
                total_val = sum(row)
                formatted_val = self.args.format % total_val
                print(f"{stacked_line}  {formatted_val}{self.args.suffix}")
            else:
                print(stacked_line)

            print()
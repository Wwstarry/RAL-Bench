import sys

# ANSI Color Codes
COLORS = {
    "red": "\033[91m",
    "blue": "\033[94m",
    "green": "\033[92m",
    "magenta": "\033[95m",
    "cyan": "\033[96m",
    "yellow": "\033[93m",
    "black": "\033[90m",
    "white": "\033[97m",
    "default": "\033[0m",
}

# Default color cycle
COLOR_CYCLE = [
    "red", "blue", "green", "magenta", "cyan", "yellow", "black", "white"
]

BLOCK = "▇"

class BaseChart:
    def __init__(self, data, args):
        self.data = data
        self.args = args

    def _print_title(self):
        if self.args.title:
            print(f"# {self.args.title}")
            print()

    def _get_color_code(self, color_name):
        return COLORS.get(color_name, COLORS["default"])

    def _get_color(self, index):
        choices = self.args.color if self.args.color else COLOR_CYCLE
        if not isinstance(choices, list):
            choices = [choices]
        
        color_name = choices[index % len(choices)]
        return self._get_color_code(color_name)

    def draw(self):
        raise NotImplementedError


class BarChart(BaseChart):
    def draw(self):
        self._print_title()
        
        # Flatten data to check for emptiness
        flat_data = [v for row in self.data.data for v in row]
        if not flat_data:
            return

        # Calculate scaling
        if self.args.different_scale:
            # Max per column
            columns = list(zip(*self.data.data))
            max_vals = []
            for col in columns:
                m = max(col)
                max_vals.append(m if m != 0 else 1)
        else:
            # Global max
            g_max = max(flat_data)
            if g_max == 0: g_max = 1
            num_cols = len(self.data.data[0]) if self.data.data else 0
            max_vals = [g_max] * num_cols

        for i, row in enumerate(self.data.data):
            label = self.data.labels[i]
            
            for j, value in enumerate(row):
                # Handle labels and indentation
                if not self.args.no_labels:
                    if j == 0:
                        print(f"{label}: ", end="")
                    else:
                        # Indent for subsequent bars in the same group
                        print(" " * (len(label) + 2), end="")
                
                # Determine max for this specific bar
                current_max = max_vals[j] if j < len(max_vals) else max_vals[0]
                
                # Calculate bar length
                # Ensure non-negative for length calculation
                val_for_len = max(0, value)
                bar_len = int((val_for_len / current_max) * self.args.width)
                
                color = self._get_color(j)
                print(f"{color}{BLOCK * bar_len}{COLORS['default']}", end="")
                
                # Print value
                if not self.args.no_values:
                    formatted = self.args.format.format(value) + self.args.suffix
                    print(f" {formatted}", end="")
                
                print()


class StackedChart(BaseChart):
    def draw(self):
        self._print_title()
        
        # Calculate global max of sums for scaling
        sums = [sum(row) for row in self.data.data]
        if not sums:
            return
        max_val = max(sums)
        if max_val == 0: max_val = 1
        
        for i, row in enumerate(self.data.data):
            label = self.data.labels[i]
            
            if not self.args.no_labels:
                print(f"{label}: ", end="")
            
            for j, value in enumerate(row):
                val_for_len = max(0, value)
                seg_len = int((val_for_len / max_val) * self.args.width)
                color = self._get_color(j)
                print(f"{color}{BLOCK * seg_len}{COLORS['default']}", end="")
            
            if not self.args.no_values:
                total = sum(row)
                formatted = self.args.format.format(total) + self.args.suffix
                print(f" {formatted}", end="")
            
            print()
import sys
from math import ceil

class BaseChart:
    """Base chart class with common functionality."""
    
    def __init__(self, data, args):
        """
        Initialize a chart.
        
        Args:
            data: Data object containing labels and values
            args: Args object with rendering options
        """
        self.data = data
        self.args = args
        self.colors = {
            'red': '\033[91m',
            'green': '\033[92m',
            'yellow': '\033[93m',
            'blue': '\033[94m',
            'magenta': '\033[95m',
            'cyan': '\033[96m',
            'white': '\033[97m',
            'reset': '\033[0m'
        }
        self.block = '█'
        
    def normalize_data(self):
        """Normalize data based on the maximum value to fit within width."""
        # Flatten data for finding max if not using different scales
        if not self.args.different_scale:
            all_values = [val for sublist in self.data.data for val in sublist]
            max_val = max(all_values) if all_values else 0
            
            normalized = []
            for row in self.data.data:
                if max_val == 0:
                    normalized.append([0] * len(row))
                else:
                    normalized.append([int((val / max_val) * self.args.width) for val in row])
            return normalized
        
        # Use different scales for each row
        normalized = []
        for row in self.data.data:
            max_val = max(row) if row else 0
            if max_val == 0:
                normalized.append([0] * len(row))
            else:
                normalized.append([int((val / max_val) * self.args.width) for val in row])
        return normalized
        
    def print_title(self):
        """Print the chart title."""
        if self.args.title:
            print(f"{self.args.title}\n")
            
    def color_block(self, block, color=None):
        """Apply color to a block if color is specified."""
        if not color or color not in self.colors:
            return block
        return f"{self.colors.get(color, '')}{block}{self.colors['reset']}"
    
    def format_value(self, value):
        """Format a value according to the format and suffix."""
        if self.args.no_values:
            return ""
        return f"{self.args.format.format(value)}{self.args.suffix}"


class BarChart(BaseChart):
    """Class for rendering horizontal bar charts."""
    
    def draw(self):
        """Render the bar chart to stdout."""
        self.print_title()
        
        if not self.data.data:
            return
            
        # Normalize data to fit within width
        normalized_data = self.normalize_data()
        
        # Get the maximum label length for alignment
        max_label_len = max([len(label) for label in self.data.labels]) if self.data.labels else 0
        
        # Print each data series
        for idx, (label, values, normalized) in enumerate(zip(
                self.data.labels, self.data.data, normalized_data)):
            
            # Print label if not hidden
            if not self.args.no_labels:
                print(f"{label.ljust(max_label_len)} │ ", end="")
            
            # Print the bar
            color = self.args.color
            bar = self.block * normalized[0] if normalized[0] > 0 else ""
            sys.stdout.write(self.color_block(bar, color))
            
            # Print the value
            if not self.args.no_values:
                print(f" {self.format_value(values[0])}")
            else:
                print()


class StackedChart(BaseChart):
    """Class for rendering stacked bar charts."""
    
    def draw(self):
        """Render the stacked bar chart to stdout."""
        self.print_title()
        
        if not self.data.data:
            return
            
        # Calculate totals for each row
        totals = [sum(row) for row in self.data.data]
        max_total = max(totals) if totals else 0
        
        # Get the maximum label length for alignment
        max_label_len = max([len(label) for label in self.data.labels]) if self.data.labels else 0
        
        # Print each data series as a stacked bar
        for idx, (label, values) in enumerate(zip(self.data.labels, self.data.data)):
            total = sum(values)
            
            # Print label if not hidden
            if not self.args.no_labels:
                print(f"{label.ljust(max_label_len)} │ ", end="")
            
            # Calculate normalized segments
            remaining_width = self.args.width
            if max_total > 0:
                remaining_width = int((total / max_total) * self.args.width)
            
            # Print the stacked bar segments
            for i, val in enumerate(values):
                if total == 0:
                    segment_width = 0
                else:
                    segment_width = int((val / total) * remaining_width) if i < len(values) - 1 else remaining_width
                    remaining_width -= segment_width
                
                color = self.args.color or f"color{i % len(self.colors)}"
                bar = self.block * segment_width if segment_width > 0 else ""
                sys.stdout.write(self.color_block(bar, color))
            
            # Print the total value
            if not self.args.no_values:
                print(f" {self.format_value(total)}")
            else:
                print()
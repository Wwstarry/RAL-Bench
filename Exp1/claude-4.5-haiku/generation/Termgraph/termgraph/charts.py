"""
Chart rendering classes for termgraph.
"""

import sys


class BarChart:
    """
    Horizontal bar chart renderer.
    """
    
    def __init__(self, data, args):
        """
        Initialize BarChart.
        
        Args:
            data: Data object containing labels and series.
            args: Args object containing rendering options.
        """
        self.data = data
        self.args = args
    
    def draw(self):
        """
        Render the bar chart to stdout.
        """
        if not self.data.series or not self.data.series[0]:
            return
        
        # Print title if provided
        if self.args.title:
            print(self.args.title)
        
        # Calculate dimensions
        num_rows = len(self.data.series)
        num_series = len(self.data.series[0]) if self.data.series else 0
        
        if num_series == 0:
            return
        
        # Find max value for scaling
        max_value = 0
        for row in self.data.series:
            for val in row:
                if val > max_value:
                    max_value = val
        
        if max_value == 0:
            max_value = 1
        
        # Calculate label width
        label_width = 0
        if not self.args.no_labels and self.data.labels:
            label_width = max(len(str(label)) for label in self.data.labels)
            label_width = max(label_width, 1)
        
        # Available width for bars
        available_width = self.args.width - label_width - 2
        if available_width < 10:
            available_width = 10
        
        # Render each row
        for row_idx, row_values in enumerate(self.data.series):
            # Print label
            if not self.args.no_labels and self.data.labels:
                label = str(self.data.labels[row_idx])
                sys.stdout.write(label.ljust(label_width) + " ")
            
            # Calculate bar width for this row
            row_max = max(row_values) if row_values else 1
            if row_max == 0:
                row_max = 1
            
            # Render bars
            bar_chars = ""
            for val in row_values:
                bar_width = int((val / row_max) * available_width)
                bar_chars += "█" * bar_width + " "
            
            sys.stdout.write(bar_chars)
            
            # Print values if not hidden
            if not self.args.no_values:
                values_str = " ".join(
                    self.args.format.format(val) + self.args.suffix
                    for val in row_values
                )
                sys.stdout.write(values_str)
            
            sys.stdout.write("\n")


class StackedChart:
    """
    Stacked horizontal bar chart renderer.
    """
    
    def __init__(self, data, args):
        """
        Initialize StackedChart.
        
        Args:
            data: Data object containing labels and series.
            args: Args object containing rendering options.
        """
        self.data = data
        self.args = args
    
    def draw(self):
        """
        Render the stacked bar chart to stdout.
        """
        if not self.data.series or not self.data.series[0]:
            return
        
        # Print title if provided
        if self.args.title:
            print(self.args.title)
        
        # Calculate dimensions
        num_rows = len(self.data.series)
        num_series = len(self.data.series[0]) if self.data.series else 0
        
        if num_series == 0:
            return
        
        # Find max total value for scaling
        max_total = 0
        for row in self.data.series:
            total = sum(row)
            if total > max_total:
                max_total = total
        
        if max_total == 0:
            max_total = 1
        
        # Calculate label width
        label_width = 0
        if not self.args.no_labels and self.data.labels:
            label_width = max(len(str(label)) for label in self.data.labels)
            label_width = max(label_width, 1)
        
        # Available width for bars
        available_width = self.args.width - label_width - 2
        if available_width < 10:
            available_width = 10
        
        # Render each row
        for row_idx, row_values in enumerate(self.data.series):
            # Print label
            if not self.args.no_labels and self.data.labels:
                label = str(self.data.labels[row_idx])
                sys.stdout.write(label.ljust(label_width) + " ")
            
            # Calculate total for this row
            row_total = sum(row_values)
            if row_total == 0:
                row_total = 1
            
            # Render stacked bars
            bar_chars = ""
            for val in row_values:
                bar_width = int((val / max_total) * available_width)
                bar_chars += "█" * bar_width
            
            sys.stdout.write(bar_chars)
            
            # Print total value if not hidden
            if not self.args.no_values:
                total_str = self.args.format.format(row_total) + self.args.suffix
                sys.stdout.write(" " + total_str)
            
            sys.stdout.write("\n")
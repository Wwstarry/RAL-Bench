"""
Chart rendering classes for termgraph
"""

import sys


class BarChart:
    """
    Horizontal bar chart renderer.
    """
    
    # Default colors for multi-series charts
    COLORS = [
        '\033[91m',  # Red
        '\033[92m',  # Green
        '\033[93m',  # Yellow
        '\033[94m',  # Blue
        '\033[95m',  # Magenta
        '\033[96m',  # Cyan
    ]
    RESET = '\033[0m'
    
    def __init__(self, data, args):
        """
        Initialize BarChart.
        
        Args:
            data: Data instance containing labels and values
            args: Args instance containing rendering options
        """
        self.data = data
        self.args = args
    
    def draw(self):
        """
        Render the bar chart to stdout.
        """
        if self.args.title:
            print(f"\n# {self.args.title}\n")
        
        # Collect all data and determine if multi-series
        all_data = []
        max_label_len = 0
        is_multi_series = False
        
        for label, values in self.data:
            if not self.args.no_labels and self.args.labels:
                max_label_len = max(max_label_len, len(str(label)))
            
            # Check if values is a list (multi-series) or single value
            if isinstance(values, (list, tuple)):
                is_multi_series = True
                all_data.append((label, list(values)))
            else:
                all_data.append((label, [values]))
        
        # Find maximum value for scaling
        if is_multi_series and not self.args.different_scale:
            # For multi-series, find max across all series
            max_val = 0
            for label, values in all_data:
                max_val = max(max_val, max(values) if values else 0)
        else:
            max_val = 0
            for label, values in all_data:
                max_val = max(max_val, max(values) if values else 0)
        
        if max_val == 0:
            max_val = 1  # Avoid division by zero
        
        # Render each row
        for label, values in all_data:
            self._draw_row(label, values, max_val, max_label_len, is_multi_series)
    
    def _draw_row(self, label, values, max_val, max_label_len, is_multi_series):
        """
        Draw a single row of the chart.
        
        Args:
            label: Row label
            values: List of numeric values for this row
            max_val: Maximum value for scaling
            max_label_len: Maximum label length for alignment
            is_multi_series: Whether this is a multi-series chart
        """
        # Print label if enabled
        if not self.args.no_labels and self.args.labels:
            label_str = str(label).ljust(max_label_len)
            print(f"{label_str} | ", end="")
        
        # Draw bars for each value in the series
        for i, value in enumerate(values):
            if value < 0:
                value = 0
            
            # Calculate bar length
            if max_val > 0:
                bar_len = int((value / max_val) * self.args.width)
            else:
                bar_len = 0
            
            # Choose color if multi-series
            if is_multi_series and self.args.color is not None:
                color = self.COLORS[i % len(self.COLORS)]
                reset = self.RESET
            else:
                color = ""
                reset = ""
            
            # Draw the bar
            bar = color + "█" * bar_len + reset
            print(bar, end="")
            
            # Print value if enabled
            if not self.args.no_values:
                formatted_value = self.args.format.format(value)
                print(f" {formatted_value}{self.args.suffix}", end="")
            
            # Add space between series if multi-series
            if is_multi_series and i < len(values) - 1:
                print(" ", end="")
        
        print()  # New line after row


class StackedChart:
    """
    Stacked horizontal bar chart renderer.
    """
    
    # Default colors for stacked segments
    COLORS = [
        '\033[91m',  # Red
        '\033[92m',  # Green
        '\033[93m',  # Yellow
        '\033[94m',  # Blue
        '\033[95m',  # Magenta
        '\033[96m',  # Cyan
    ]
    RESET = '\033[0m'
    
    def __init__(self, data, args):
        """
        Initialize StackedChart.
        
        Args:
            data: Data instance containing labels and values
            args: Args instance containing rendering options
        """
        self.data = data
        self.args = args
    
    def draw(self):
        """
        Render the stacked bar chart to stdout.
        """
        if self.args.title:
            print(f"\n# {self.args.title}\n")
        
        # Collect all data
        all_data = []
        max_label_len = 0
        max_total = 0
        
        for label, values in self.data:
            if not self.args.no_labels and self.args.labels:
                max_label_len = max(max_label_len, len(str(label)))
            
            # Ensure values is a list
            if isinstance(values, (list, tuple)):
                values_list = list(values)
            else:
                values_list = [values]
            
            # Calculate total for this row
            total = sum(v if v > 0 else 0 for v in values_list)
            max_total = max(max_total, total)
            
            all_data.append((label, values_list, total))
        
        if max_total == 0:
            max_total = 1  # Avoid division by zero
        
        # Render each row
        for label, values, total in all_data:
            self._draw_row(label, values, total, max_total, max_label_len)
    
    def _draw_row(self, label, values, total, max_total, max_label_len):
        """
        Draw a single stacked row.
        
        Args:
            label: Row label
            values: List of numeric values to stack
            total: Total of all values in this row
            max_total: Maximum total across all rows
            max_label_len: Maximum label length for alignment
        """
        # Print label if enabled
        if not self.args.no_labels and self.args.labels:
            label_str = str(label).ljust(max_label_len)
            print(f"{label_str} | ", end="")
        
        # Calculate total bar length
        if max_total > 0:
            total_bar_len = int((total / max_total) * self.args.width)
        else:
            total_bar_len = 0
        
        # Calculate proportional lengths for each segment
        segments = []
        remaining_len = total_bar_len
        
        for i, value in enumerate(values):
            if value < 0:
                value = 0
            
            if total > 0:
                # Calculate this segment's proportion
                segment_len = int((value / total) * total_bar_len)
                
                # Adjust last segment to use remaining length
                if i == len(values) - 1:
                    segment_len = remaining_len
                else:
                    remaining_len -= segment_len
                
                segments.append((value, segment_len, i))
            else:
                segments.append((value, 0, i))
        
        # Draw stacked segments
        for value, seg_len, i in segments:
            if self.args.color is not None:
                color = self.COLORS[i % len(self.COLORS)]
                reset = self.RESET
            else:
                color = ""
                reset = ""
            
            bar = color + "█" * seg_len + reset
            print(bar, end="")
        
        # Print total value if enabled
        if not self.args.no_values:
            formatted_total = self.args.format.format(total)
            print(f" {formatted_total}{self.args.suffix}", end="")
        
        print()  # New line after row
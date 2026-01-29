"""
Chart rendering classes.
"""

import sys
from typing import List, Union
from .data import Data
from .args import Args


class BarChart:
    """
    Base class for rendering bar charts.
    """
    
    # ANSI color codes for colored output
    COLORS = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'magenta': '\033[95m',
        'cyan': '\033[96m',
        'black': '\033[90m',
        'white': '\033[97m',
        'reset': '\033[0m'
    }
    
    DEFAULT_COLORS = ['blue', 'green', 'red', 'cyan', 'magenta', 'yellow']
    
    def __init__(self, data: Data, args: Args):
        """
        Initialize BarChart.
        
        Args:
            data: Data object containing labels and values
            args: Args object containing rendering options
        """
        self.data = data
        self.args = args
        
        # Set up colors
        self.colors = self.args.color or self.DEFAULT_COLORS
        
        # Ensure we have enough colors
        while len(self.colors) < self.data.num_series:
            self.colors.extend(self.DEFAULT_COLORS)
    
    def draw(self) -> None:
        """Draw the chart to stdout."""
        if self.args.vertical:
            self._draw_vertical()
        else:
            self._draw_horizontal()
    
    def _draw_horizontal(self) -> None:
        """Draw horizontal bar chart."""
        if self.args.title:
            print(self.args.title)
            print()
        
        # Calculate scaling factor
        max_val = self.data.get_max_value()
        scale = self.args.width / max_val if max_val > 0 else 1
        
        for i, label in enumerate(self.data.labels):
            # Print label
            if not self.args.no_labels:
                print(f"{label}: ", end="")
            
            # Print bars for each series
            if self.data.num_series == 1:
                # Single series
                value = self.data.data[0][i]
                bar_length = int(value * scale)
                bar = self._create_bar(bar_length, 0)
                
                # Print value if requested
                if not self.args.no_values:
                    formatted_value = self.args.format.format(value) + self.args.suffix
                    print(f"{bar} {formatted_value}")
                else:
                    print(bar)
            else:
                # Multiple series
                for series_idx in range(self.data.num_series):
                    value = self.data.data[series_idx][i]
                    bar_length = int(value * scale)
                    bar = self._create_bar(bar_length, series_idx)
                    
                    # Print value if requested
                    if not self.args.no_values:
                        formatted_value = self.args.format.format(value) + self.args.suffix
                        print(f"{bar} {formatted_value}", end="")
                    else:
                        print(bar, end="")
                    
                    if series_idx < self.data.num_series - 1:
                        print(" ", end="")
                print()
    
    def _draw_vertical(self) -> None:
        """Draw vertical bar chart."""
        if self.args.title:
            print(self.args.title)
            print()
        
        # Calculate scaling factor
        max_val = self.data.get_max_value()
        scale = self.args.width / max_val if max_val > 0 else 1
        
        # For vertical charts, we need to build from top to bottom
        max_bar_height = self.args.width
        
        # Create grid for rendering
        grid = [[' ' for _ in range(self.data.num_labels)] 
                for _ in range(max_bar_height)]
        
        # Fill grid with bars
        for label_idx in range(self.data.num_labels):
            for series_idx in range(self.data.num_series):
                value = self.data.data[series_idx][label_idx]
                bar_height = int(value * scale)
                
                # Fill from bottom up
                for h in range(bar_height):
                    if h < max_bar_height:
                        grid[max_bar_height - 1 - h][label_idx] = '█'
        
        # Print grid
        for row in grid:
            print(''.join(row))
        
        # Print labels if requested
        if not self.args.no_labels:
            print()
            for label in self.data.labels:
                print(label[:1], end=" ")  # Just first character for vertical
            print()
    
    def _create_bar(self, length: int, series_idx: int) -> str:
        """
        Create a bar string of given length with appropriate color.
        
        Args:
            length: Length of bar in characters
            series_idx: Index of data series for color selection
            
        Returns:
            Colored bar string
        """
        color_name = self.colors[series_idx % len(self.colors)]
        color_code = self.COLORS.get(color_name, '')
        reset_code = self.COLORS['reset']
        
        bar_char = '█' if not self.args.histogram else '▇'
        bar = bar_char * length
        
        if color_code and sys.stdout.isatty():
            return f"{color_code}{bar}{reset_code}"
        return bar
    
    def _format_value(self, value: Union[int, float]) -> str:
        """
        Format a numeric value according to args.
        
        Args:
            value: Numeric value to format
            
        Returns:
            Formatted string
        """
        return self.args.format.format(value) + self.args.suffix


class StackedChart(BarChart):
    """
    Class for rendering stacked bar charts.
    """
    
    def _draw_horizontal(self) -> None:
        """Draw horizontal stacked bar chart."""
        if self.args.title:
            print(self.args.title)
            print()
        
        # Calculate scaling factor based on max total per label
        max_total = 0
        for i in range(self.data.num_labels):
            total = sum(series[i] for series in self.data.data)
            if total > max_total:
                max_total = total
        
        scale = self.args.width / max_total if max_total > 0 else 1
        
        for i, label in enumerate(self.data.labels):
            # Print label
            if not self.args.no_labels:
                print(f"{label}: ", end="")
            
            # Calculate cumulative bar segments
            cumulative_length = 0
            bar_parts = []
            
            for series_idx in range(self.data.num_series):
                value = self.data.data[series_idx][i]
                segment_length = int(value * scale)
                
                if segment_length > 0:
                    bar_part = self._create_bar(segment_length, series_idx)
                    bar_parts.append(bar_part)
                    cumulative_length += segment_length
            
            # Combine bar parts
            full_bar = ''.join(bar_parts)
            
            # Print bar and total value if requested
            if not self.args.no_values:
                total_value = sum(series[i] for series in self.data.data)
                formatted_value = self.args.format.format(total_value) + self.args.suffix
                print(f"{full_bar} {formatted_value}")
            else:
                print(full_bar)
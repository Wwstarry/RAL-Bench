import sys
from .data import Data
from .args import Args

class BarChart:
    def __init__(self, data: Data, args: Args):
        self.data = data
        self.args = args
    
    def draw(self):
        if self.args.vertical:
            self._draw_vertical()
        else:
            self._draw_horizontal()
    
    def _draw_horizontal(self):
        if self.args.title:
            print(self.args.title)
        
        max_value = max(max(series) for series in self.data.data) if self.data.data else 0
        if max_value == 0:
            max_value = 1
        
        for i, label in enumerate(self.data.labels):
            if not self.args.no_labels:
                print(f"{label}: ", end="")
            
            values = [series[i] for series in self.data.data]
            total = sum(values)
            
            if self.args.stacked:
                self._draw_stacked_bar(values, total, max_value)
            else:
                for j, value in enumerate(values):
                    if j > 0:
                        print(" ", end="")
                    self._draw_single_bar(value, max_value, j)
                print()
            
            if not self.args.no_values:
                value_str = self.args.format.format(total) + self.args.suffix
                print(f" {value_str}")
            else:
                print()
    
    def _draw_vertical(self):
        if self.args.title:
            print(self.args.title)
        
        max_value = max(max(series) for series in self.data.data) if self.data.data else 0
        if max_value == 0:
            max_value = 1
        
        # Transpose data for vertical rendering
        transposed_data = list(zip(*self.data.data)) if self.data.data else []
        
        for row in range(self.args.width, -1, -1):
            threshold = (row / self.args.width) * max_value
            
            for values in transposed_data:
                if self.args.stacked:
                    total = sum(values)
                    if total >= threshold:
                        print("█", end="")
                    else:
                        print(" ", end="")
                else:
                    for value in values:
                        if value >= threshold:
                            print("█", end="")
                        else:
                            print(" ", end="")
                    print(" ", end="")
            print()
        
        if not self.args.no_labels:
            for label in self.data.labels:
                print(label, end=" ")
            print()
    
    def _draw_stacked_bar(self, values, total, max_value):
        bar_length = int((total / max_value) * self.args.width)
        for i in range(self.args.width):
            if i < bar_length:
                print("█", end="")
            else:
                print(" ", end="")
        print()
    
    def _draw_single_bar(self, value, max_value, color_index):
        bar_length = int((value / max_value) * self.args.width)
        for i in range(self.args.width):
            if i < bar_length:
                print("█", end="")
            else:
                print(" ", end="")


class StackedChart(BarChart):
    def __init__(self, data: Data, args: Args):
        super().__init__(data, args)
        self.args.stacked = True
#!/usr/bin/env python3
import sys
import argparse
from .data import Data
from .args import Args
from .charts import BarChart, StackedChart

def main():
    parser = argparse.ArgumentParser(description='Draw basic graphs on terminal')
    parser.add_argument('--width', type=int, default=50, help='width of graph in characters')
    parser.add_argument('--stacked', action='store_true', help='stacked bar graph')
    parser.add_argument('--different-scale', action='store_true', help='categories have different scales')
    parser.add_argument('--no-labels', action='store_true', help='disable labels')
    parser.add_argument('--format', type=str, default='{:>5.2f}', help='format specifier for values')
    parser.add_argument('--suffix', type=str, default='', help='string to add as a suffix to all values')
    parser.add_argument('--vertical', action='store_true', help='vertical graph')
    parser.add_argument('--histogram', action='store_true', help='histogram')
    parser.add_argument('--no-values', action='store_true', help='disable printing values at the end')
    parser.add_argument('--color', nargs='+', help='colors for the series')
    parser.add_argument('--title', type=str, default='', help='title of graph')
    
    args = parser.parse_args()
    
    # Read data from stdin
    labels = []
    data_series = []
    
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
            
        parts = line.split()
        if not parts:
            continue
            
        labels.append(parts[0])
        values = [float(x) for x in parts[1:]]
        data_series.append(values)
    
    # Transpose data if we have multiple series
    if data_series:
        num_series = len(data_series[0])
        data = []
        for i in range(num_series):
            series = [row[i] for row in data_series]
            data.append(series)
    else:
        data = []
    
    chart_args = Args(
        width=args.width,
        stacked=args.stacked,
        different_scale=args.different_scale,
        no_labels=args.no_labels,
        format=args.format,
        suffix=args.suffix,
        vertical=args.vertical,
        histogram=args.histogram,
        no_values=args.no_values,
        color=args.color or [],
        labels=labels,
        title=args.title
    )
    
    chart_data = Data(labels=labels, data=data)
    
    if args.stacked:
        chart = StackedChart(chart_data, chart_args)
    else:
        chart = BarChart(chart_data, chart_args)
    
    chart.draw()

if __name__ == '__main__':
    main()
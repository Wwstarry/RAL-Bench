#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CLI interface for termgraph
"""

import argparse
import sys
import csv
from termgraph.data import Data
from termgraph.args import Args
from termgraph.charts import BarChart, StackedChart

def main():
    """Main function for CLI execution."""
    parser = argparse.ArgumentParser(
        description='Plot a bar chart in the terminal')
    
    parser.add_argument(
        'data_file', nargs='?', default='-',
        help='Data file (or stdin)')
    
    parser.add_argument(
        '--width', type=int, default=50,
        help='Width of the chart in character cells')
    
    parser.add_argument(
        '--stacked', action='store_true',
        help='Use stacked bars')
    
    parser.add_argument(
        '--different-scale', action='store_true',
        help='Use different scales for each data series')
    
    parser.add_argument(
        '--no-labels', action='store_true',
        help='Hide labels')
    
    parser.add_argument(
        '--format', default='{:.0f}',
        help='Format string for values')
    
    parser.add_argument(
        '--suffix', default='',
        help='Suffix to append to values')
    
    parser.add_argument(
        '--vertical', action='store_true',
        help='Use vertical orientation')
    
    parser.add_argument(
        '--histogram', action='store_true',
        help='Display as histogram')
    
    parser.add_argument(
        '--no-values', action='store_true',
        help='Hide values')
    
    parser.add_argument(
        '--color', 
        help='Color for the chart')
    
    parser.add_argument(
        '--title', default='',
        help='Title for the chart')
    
    args = parser.parse_args()
    
    # Simple implementation to read from stdin or file
    if args.data_file == '-':
        data_source = sys.stdin
    else:
        data_source = open(args.data_file, 'r')
    
    try:
        reader = csv.reader(data_source)
        labels = []
        data = []
        
        for row in reader:
            if not row:
                continue
            labels.append(row[0])
            data.append([float(val) for val in row[1:] if val.strip()])
        
        chart_data = Data(labels, data)
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
            color=args.color,
            title=args.title
        )
        
        if args.stacked:
            chart = StackedChart(chart_data, chart_args)
        else:
            chart = BarChart(chart_data, chart_args)
        
        chart.draw()
    
    finally:
        if args.data_file != '-':
            data_source.close()

if __name__ == "__main__":
    main()
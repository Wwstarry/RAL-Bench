# termgraph/cli.py

import argparse
from . import data, args, charts

def main():
    """Main function for the termgraph command-line interface."""
    parser = argparse.ArgumentParser(
        description='A Python command-line tool for drawing basic graphs in the terminal.'
    )
    
    parser.add_argument('--title', type=str, help='Title of the chart.')
    parser.add_argument('--width', type=int, default=50, help='Width of the chart.')
    parser.add_argument('--format', type=str, default='{:<5.2f}', help='Format specifier for values.')
    parser.add_argument('--suffix', type=str, default='', help='Suffix to append to values.')
    parser.add_argument('--no-labels', action='store_true', help='Do not print labels.')
    parser.add_argument('--no-values', action='store_true', help='Do not print values.')
    parser.add_argument('--color', nargs='*', help='Colors for the bars (e.g., red, green).')
    parser.add_argument('--vertical', action='store_true', help='Draw a vertical chart (not implemented).')
    parser.add_argument('--stacked', action='store_true', help='Draw a stacked chart.')
    parser.add_argument('--different-scale', action='store_true', help='Use a different scale for each series.')
    parser.add_argument('--histogram', action='store_true', help='Draw a histogram (not implemented).')
    parser.add_argument('filename', nargs='?', help='Data file to read from (not implemented).')

    parsed_args = parser.parse_args()

    # This is a mock CLI to demonstrate library usage.
    # It does not implement file reading or full command-line functionality.
    print("--- This is a mock CLI. To use the library, import it in your Python code. ---")
    print("--- Example: ---")
    
    # 1. Prepare data
    labels = ['2020', '2021', '2022', '2023']
    series_data = [[10.5, 40.1, 25.0, 30.3], [20.0, 15.5, 35.8, 25.1]]
    chart_data = data.Data(series_data, labels)

    # 2. Prepare arguments using the Args class
    chart_args = args.Args(
        width=parsed_args.width,
        title="Sample Chart From CLI",
        stacked=parsed_args.stacked,
        color=parsed_args.color or ['blue', 'red'],
        no_labels=parsed_args.no_labels,
        format=parsed_args.format,
        suffix=parsed_args.suffix,
        different_scale=parsed_args.different_scale,
        no_values=parsed_args.no_values
    )
    
    # 3. Create and draw the chart
    if chart_args.stacked:
        chart = charts.StackedChart(chart_data, chart_args)
    else:
        chart = charts.BarChart(chart_data, chart_args)
    
    chart.draw()

if __name__ == '__main__':
    main()
import argparse
import sys
from .core import tabulate

def main():
    parser = argparse.ArgumentParser(description='Pretty-print tabular data')
    parser.add_argument('-H', '--headers', action='store_true', help='Use the first row as headers')
    parser.add_argument('-s', '--sep', default=' ', help='Field separator (default: " ")')
    parser.add_argument('-f', '--format', default='plain', help='Table format (default: plain)')
    parser.add_argument('file', nargs='?', type=argparse.FileType('r'), default=sys.stdin, 
                        help='Input file (default: stdin)')

    args = parser.parse_args()

    data = []
    for line in args.file:
        fields = line.strip().split(args.sep)
        data.append(fields)

    headers = None
    if args.headers and data:
        headers = data[0]
        data = data[1:]

    print(tabulate(data, headers=headers, tablefmt=args.format))

if __name__ == '__main__':
    main()
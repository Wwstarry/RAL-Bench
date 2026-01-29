import sys
import json
import argparse

from .core import tabulate

def main(argv=None):
    parser = argparse.ArgumentParser(description="Format tabular data using a tabulate-like formatter.")
    parser.add_argument("-f", "--format", dest="tablefmt", default="simple",
                        help="Table format: plain, simple, grid, pipe, tsv, csv, html")
    parser.add_argument("--headers", dest="headers", default=None,
                        help="Headers: 'firstrow', 'keys', or JSON array of strings")
    parser.add_argument("--floatfmt", dest="floatfmt", default="g", help="Float format spec (default: g)")
    parser.add_argument("--numalign", dest="numalign", default="right", help="Numeric alignment (left/right/center/decimal)")
    parser.add_argument("--stralign", dest="stralign", default="left", help="String alignment (left/right/center)")
    parser.add_argument("--missingval", dest="missingval", default="", help="String for missing values (default: empty)")
    parser.add_argument("infile", nargs="?", default="-", help="Input file with JSON data (default: stdin)")
    args = parser.parse_args(argv)

    # parse headers option
    headers = None
    if args.headers is None:
        headers = ()
    else:
        h = args.headers.strip()
        if h in ("firstrow", "keys"):
            headers = h
        else:
            try:
                headers = json.loads(h)
            except Exception:
                # fallback: comma-separated
                headers = [p.strip() for p in h.split(",") if p.strip()]

    # Load tabular data from JSON
    if args.infile == "-" or args.infile == "":
        data_str = sys.stdin.read()
    else:
        with open(args.infile, "r", encoding="utf-8") as f:
            data_str = f.read()
    try:
        data = json.loads(data_str)
    except Exception as e:
        sys.stderr.write("Failed to parse input as JSON: %s\n" % e)
        sys.exit(1)

    out = tabulate(
        data,
        headers=headers,
        tablefmt=args.tablefmt,
        floatfmt=args.floatfmt,
        numalign=args.numalign,
        stralign=args.stralign,
        missingval=args.missingval,
    )
    sys.stdout.write(out)
    if not out.endswith("\n"):
        sys.stdout.write("\n")


if __name__ == "__main__":
    main()
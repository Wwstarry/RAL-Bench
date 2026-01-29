import argparse
from lib.core.data import cmdLineOptions

def cmdLineParser():
    parser = argparse.ArgumentParser(
        description="A simple SQL injection testing tool.",
        add_help=False
    )
    parser.add_argument("-h", "--help", action="help", help="Show this help message and exit")
    parser.add_argument("-hh", "--advanced-help", action="store_true", help="Show advanced help message")
    parser.add_argument("--version", action="store_true", help="Show program's version number and exit")
    
    args, unknown = parser.parse_known_args()
    
    if args.advanced_help:
        print("Advanced help: This is a SQL injection testing tool.")
        exit(0)
    if args.version:
        from lib.core.settings import VERSION
        print(f"Version: {VERSION}")
        exit(0)
    
    cmdLineOptions.update(vars(args))
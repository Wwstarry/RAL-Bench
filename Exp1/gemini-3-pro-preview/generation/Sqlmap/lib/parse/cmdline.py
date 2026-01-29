import argparse
import sys
from lib.core.settings import VERSION, DESCRIPTION

def cmdLineParser():
    """
    Parses command line arguments.
    """
    # Disable default help to handle -h and -hh manually
    parser = argparse.ArgumentParser(description=DESCRIPTION, add_help=False)
    
    # Use action='count' to distinguish between -h (1) and -hh (2)
    parser.add_argument("-h", "--help", action="count", default=0, help="Show basic help message and exit")
    parser.add_argument("--version", action="store_true", help="Show program's version number and exit")
    
    # Standard sqlmap arguments (subset for compatibility)
    parser.add_argument("-u", "--url", help="Target URL (e.g. \"http://www.site.com/vuln.php?id=1\")")
    parser.add_argument("-v", "--verbose", type=int, default=1, help="Verbosity level: 0-6 (default 1)")
    
    try:
        args = parser.parse_args()
    except SystemExit:
        # argparse exits on error
        raise
    except Exception as e:
        print(f"Error parsing arguments: {e}")
        sys.exit(1)

    if args.version:
        print(f"sqlmap/{VERSION}")
        sys.exit(0)

    if args.help > 0:
        print(f"sqlmap/{VERSION} - {DESCRIPTION}")
        print("\nUsage: python sqlmap.py [options]")
        print("\nOptions:")
        print("  -h, --help            Show basic help message and exit")
        print("  -hh                   Show advanced help message and exit")
        print("  --version             Show program's version number and exit")
        print("  -v VERBOSE            Verbosity level: 0-6 (default 1)")
        print("  -u URL, --url=URL     Target URL (e.g. \"http://www.site.com/vuln.php?id=1\")")
        
        if args.help > 1:
            print("\nAdvanced Options:")
            print("  (Mock advanced options placeholder)")
            
        sys.exit(0)

    return args
"""
Copyright (c) 2006-2024 sqlmap developers (https://sqlmap.org/)
See the file 'LICENSE' for copying permission
"""

import argparse
import sys
from lib.core.settings import VERSION, DESCRIPTION

def cmdLineParser():
    """Parse command line arguments"""
    
    parser = argparse.ArgumentParser(
        description=DESCRIPTION,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False
    )
    
    # Basic options
    parser.add_argument("-h", "--help", action="store_true", 
                       help="Show basic help message and exit")
    parser.add_argument("-hh", action="store_true", 
                       help="Show advanced help message and exit")
    parser.add_argument("--version", action="store_true", 
                       help="Show program's version number and exit")
    
    # Target specification
    parser.add_argument("-u", "--url", help="Target URL")
    parser.add_argument("-g", "--google-dork", help="Process Google dork results")
    
    # Request configuration
    parser.add_argument("--data", help="Data string to be sent via POST")
    parser.add_argument("--cookie", help="HTTP Cookie header value")
    parser.add_argument("--random-agent", action="store_true", 
                       help="Use randomly selected HTTP User-Agent header value")
    parser.add_argument("--proxy", help="Use a proxy to connect to the target URL")
    
    # Injection configuration
    parser.add_argument("-p", "--parameter", help="Testable parameter(s)")
    parser.add_argument("--dbms", help="Force back-end DBMS to this value")
    
    # Enumeration options
    parser.add_argument("--current-user", action="store_true", 
                       help="Retrieve DBMS current user")
    parser.add_argument("--current-db", action="store_true", 
                       help="Retrieve DBMS current database")
    parser.add_argument("--dbs", action="store_true", 
                       help="Enumerate DBMS databases")
    parser.add_argument("--tables", action="store_true", 
                       help="Enumerate DBMS database tables")
    parser.add_argument("--columns", action="store_true", 
                       help="Enumerate DBMS database table columns")
    parser.add_argument("--dump", action="store_true", 
                       help="Dump DBMS database table entries")
    
    # Additional options
    parser.add_argument("--batch", action="store_true", 
                       help="Never ask for user input, use the default behavior")
    parser.add_argument("--flush-session", action="store_true", 
                       help="Flush session files for current target")
    parser.add_argument("--output-dir", help="Custom output directory path")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Handle help and version flags
    if args.help:
        parser.print_help()
        sys.exit(0)
    
    if args.hh:
        # Advanced help - show all options
        parser.print_help()
        print("\n" + "="*80)
        print("Advanced Options:")
        print("  --level=LEVEL       Level of tests to perform (1-5, default 1)")
        print("  --risk=RISK         Risk of tests to perform (1-3, default 1)")
        print("  --technique=TECH    SQL injection techniques to use")
        print("  --time-sec=TIMESEC  Seconds to delay the response")
        print("  --union-cols=UCOLS  Range of columns to test for UNION query")
        print("  --os-shell          Prompt for an interactive operating system shell")
        print("  --os-pwn            Prompt for an OOB shell, Meterpreter or VNC")
        sys.exit(0)
    
    if args.version:
        print(f"sqlmap version {VERSION}")
        sys.exit(0)
    
    return args
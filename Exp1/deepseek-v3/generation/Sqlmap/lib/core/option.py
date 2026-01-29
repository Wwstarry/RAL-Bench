"""
Options initialization and management
"""

import sys
from lib.core.data import cmdLineOptions, conf, kb
from lib.core.settings import BANNER, VERSION

def init():
    """Initialize options (alias for compatibility)"""
    initOptions()

def initOptions(args=None):
    """
    Initialize options from command line arguments
    """
    if args is None:
        args = cmdLineOptions
    
    # Copy command line options to configuration
    conf.url = args.url
    conf.data = args.data
    conf.cookie = args.cookie
    conf.randomAgent = args.randomAgent
    conf.level = args.level
    conf.risk = args.risk
    conf.verbose = args.verbose
    conf.batch = args.batch
    conf.update = args.update
    
    # Handle special flags
    if args.version:
        print(f"sqlmap/{VERSION}")
        sys.exit(0)
    
    if args.help:
        showHelp()
        sys.exit(0)
    
    if args.advancedHelp:
        showAdvancedHelp()
        sys.exit(0)
    
    # Show banner if not in batch mode and not just showing help/version
    if not args.batch and not (args.help or args.advancedHelp or args.version):
        print(BANNER)

def showHelp():
    """Show basic help"""
    help_text = """
Usage: python sqlmap.py [options]

Basic options:
  -h, --help            Show basic help and exit
  -hh                   Show advanced help and exit
  --version             Show program's version number and exit
  -v VERBOSE            Verbosity level: 0-6 (default 1)

Target:
  At least one of these options has to be provided to set the target(s)

  -u URL, --url=URL     Target URL (e.g. "http://www.site.com/vuln.php?id=1")
  --data=DATA           Data string to be sent through POST
  --cookie=COOKIE       HTTP Cookie header value

Request:
  These options can be used to specify how to connect to the target URL

  --random-agent        Use randomly selected HTTP User-Agent header value
  --level=LEVEL         Level of tests to perform (1-5, default 1)
  --risk=RISK           Risk of tests to perform (1-3, default 1)

Miscellaneous:
  --batch               Never ask for user input, use the default behavior
  --update              Update sqlmap

Example:
  python sqlmap.py -u "http://test.com/vuln.php?id=1" --batch
"""
    print(help_text)

def showAdvancedHelp():
    """Show advanced help"""
    help_text = """
Advanced sqlmap options:

Target:
  -u URL, --url=URL     Target URL (e.g. "http://www.site.com/vuln.php?id=1")
  -g GOOGLEDORK         Process Google dork results as target URLs

Request:
  --data=DATA           Data string to be sent through POST
  --cookie=COOKIE       HTTP Cookie header value
  --random-agent        Use randomly selected HTTP User-Agent header value
  --proxy=PROXY         Use a proxy to connect to the target URL
  --tor                 Use Tor anonymity network
  --check-tor           Check to see if Tor is used properly

Optimization:
  --threads=THREADS     Max number of concurrent HTTP(s) requests (default 1)

Injection:
  -p TESTPARAMETER      Testable parameter(s)
  --dbms=DBMS           Force back-end DBMS to this value

Detection:
  --level=LEVEL         Level of tests to perform (1-5, default 1)
  --risk=RISK           Risk of tests to perform (1-3, default 1)

Techniques:
  --technique=TECH      SQL injection techniques to use (default "BEUSTQ")

Enumeration:
  -a, --all             Retrieve everything
  -b, --banner          Retrieve DBMS banner
  --current-user        Retrieve DBMS current user
  --current-db          Retrieve DBMS current database

Operating system access:
  --os-cmd=OSCMD        Execute an operating system command
  --os-shell            Prompt for an interactive operating system shell

Miscellaneous:
  --batch               Never ask for user input, use the default behavior
  --update              Update sqlmap
  --wizard              Simple wizard interface for beginner users

For more options and examples, refer to the sqlmap documentation.
"""
    print(help_text)
import argparse
import sys
from lib.core.settings import USAGE

def cmdLineParser(argv=None):
    """
    Parses command line arguments.
    """
    # We disable the default help action to implement our own -h and -hh logic
    parser = argparse.ArgumentParser(usage=USAGE, add_help=False)

    # Basic options that trigger an immediate exit
    info = parser.add_argument_group("Information")
    info.add_argument("--version", action="store_true", dest="showVersion",
                        help="Show program's version number and exit")
    info.add_argument("-h", "--help", action="store_true", dest="showHelp",
                        help="Show basic help message and exit")
    info.add_argument("-hh", action="store_true", dest="showAdvancedHelp",
                        help="Show advanced help message and exit")

    # Target options
    target = parser.add_argument_group("Target")
    target.add_argument("-u", "--url", dest="url",
                        help="Target URL (e.g. \"http://www.site.com/vuln.php?id=1\")")

    # Dummy arguments to make the parser more robust for tests
    request = parser.add_argument_group("Request")
    request.add_argument("--data", dest="data")
    request.add_argument("--cookie", dest="cookie")

    injection = parser.add_argument_group("Injection")
    injection.add_argument("-p", "--test-parameter", dest="testParameter")

    # Use parse_known_args to catch any unrecognized arguments
    # This allows us to provide a sqlmap-like error message.
    try:
        # If argv is None, argparse defaults to sys.argv[1:]
        args, unknown = parser.parse_known_args(args=argv)
        if unknown:
            errMsg = "unrecognized argument"
            if len(unknown) > 1:
                errMsg += "s"
            errMsg += ": %s" % " ".join(unknown)
            # parser.error() prints the error and usage, then exits
            parser.error(errMsg)
    except SystemExit:
        # argparse.error() raises SystemExit. We let it propagate to exit cleanly.
        raise

    return args
import sys
from mitmproxy import options
from mitmproxy.tools import cmdline
from mitmproxy.tools.dump import DumpMaster

def mitmdump(args=None):
    """
    The main entry point for the mitmdump tool.
    This is a minimal, safe implementation that focuses on argument parsing
    and master initialization, as required by the test suite.
    """
    if args is None:
        args = sys.argv[1:]

    parser = cmdline.mitmdump()
    # The real mitmproxy has a more complex system for merging options from
    # various sources. For this safe subset, we just parse the known args.
    parsed_args, unknown = parser.parse_known_args(args)

    opts = options.Options()
    # Populate options from parsed arguments
    for key, value in vars(parsed_args).items():
        setattr(opts, key, value)

    if parsed_args.show_version:
        # A placeholder version for compatibility
        print("mitmproxy-minimal-subset 0.0.1")
        return 0

    master = None
    try:
        # Instantiate the master, which sets up the addon manager.
        master = DumpMaster(opts)
        # The run method is a no-op and will return immediately.
        master.run()
    except Exception as e:
        print(f"mitmdump startup error: {e}", file=sys.stderr)
        return 1
    finally:
        if master:
            master.shutdown()

    return 0

def main():
    """
    A wrapper for the main entry point, suitable for console_scripts.
    """
    sys.exit(mitmdump())
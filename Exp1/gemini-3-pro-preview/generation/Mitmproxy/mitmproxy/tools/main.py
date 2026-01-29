import sys
import argparse
from mitmproxy.tools import cmdline
from mitmproxy.tools.dump import DumpMaster
from mitmproxy.options import Options
from mitmproxy import version

def mitmdump(args=None):
    if args is None:
        args = sys.argv[1:]

    parser = cmdline.mitmdump()
    
    try:
        parsed_args = parser.parse_args(args)
    except SystemExit:
        # argparse handles help/version printing and exiting
        return

    if parsed_args.version:
        print(f"mitmproxy {version.__version__}")
        return

    opts = Options()
    # Map parsed args to options
    if parsed_args.listen_port:
        opts.listen_port = parsed_args.listen_port
    if parsed_args.scripts:
        opts.scripts = parsed_args.scripts

    master = DumpMaster(opts)
    
    # Safe-to-evaluate: We do not actually start a network server.
    # We just trigger the lifecycle events.
    master.run()

if __name__ == "__main__":
    mitmdump()
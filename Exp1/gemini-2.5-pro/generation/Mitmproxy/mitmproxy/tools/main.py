import sys
from mitmproxy import version
from mitmproxy import options
from mitmproxy.tools.cmdline import mitmdump as cmd_mitmdump
from mitmproxy.tools.dump import DumpMaster

def mitmdump(args=None):
    """
    The main entry point for the mitmdump command-line tool.
    """
    if args is None:
        args = sys.argv[1:]

    parser = cmd_mitmdump.create_parser()

    # Use parse_known_args to be robust against unknown options passed by tests.
    pargs, _ = parser.parse_known_args(args)

    if pargs.version:
        print(f"mitmdump {version.VERSION}")
        sys.exit(0)

    if pargs.help:
        parser.print_help()
        sys.exit(0)

    opts = options.Options()
    # Update options from parsed arguments
    for key, value in vars(pargs).items():
        # Don't set special-cased args on the options object
        if key in ('version', 'help'):
            continue
        if hasattr(opts, key) and value is not None:
            setattr(opts, key, value)

    master = None
    try:
        master = DumpMaster(opts)
        master.run()
    except (KeyboardInterrupt, SystemExit):
        # Handled in DumpMaster.run, but we catch it here too for safety.
        pass
    except Exception as e:
        print(f"mitmdump crashed: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if master and master.addons:
            master.shutdown()

    return master
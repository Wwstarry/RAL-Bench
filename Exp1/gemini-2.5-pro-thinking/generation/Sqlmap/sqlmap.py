#!/usr/bin/env python3

import sys
import time

def main():
    """
    Main function - the entry point of the script.
    """
    try:
        # These imports are placed inside main() to mimic the structure of the
        # reference sqlmap project, which helps in managing dependencies and
        # ensuring a clean global namespace.
        from lib.core.data import kb, conf
        from lib.core.settings import DESCRIPTION, VERSION
        from lib.parse.cmdline import cmdLineParser
        from lib.core.option import initOptions, init
        from lib.controller.controller import start

        # Store the original command line for logging/reporting purposes.
        kb.original_cmdline = " ".join(sys.argv)

        # Parse the command-line arguments. This function will exit if
        # --help, --version, or invalid arguments are provided.
        cmd_line_options = cmdLineParser()

        # Initialize the global state objects (cmdLineOptions, conf, kb)
        # with the parsed options.
        initOptions(cmd_line_options)
        init()

        # Print a startup banner, similar to the real tool.
        print(f"{DESCRIPTION} ({VERSION})")
        print("[*] starting @ %s\n" % time.strftime("%X /%Y-%m-%d/"))

        # Pass control to the main controller function.
        start()

    except KeyboardInterrupt:
        print("\n[*] User aborted.")
    except SystemExit:
        # This is raised by argparse for actions like --help, so we let it pass.
        pass
    except Exception as e:
        # A simple catch-all for any other unexpected errors.
        print(f"[!] Unhandled exception: {e}", file=sys.stderr)
    finally:
        # Print a shutdown message, ensuring it always runs.
        print("\n[*] shutting down at %s" % time.strftime("%X /%Y-%m-%d/"))

if __name__ == '__main__':
    main()
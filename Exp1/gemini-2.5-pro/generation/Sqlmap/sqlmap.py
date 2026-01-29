#!/usr/bin/env python3

import sys
import time

from lib.core.common import unhandledExceptionMessage
from lib.core.data import cmdLineOptions, conf, kb, logger
from lib.core.option import init
from lib.controller.controller import start
from lib.parse.cmdline import cmdLineParser

def main():
    """
    Main function of sqlmap when running from command line.
    """
    try:
        # Store the start time for any time-based calculations
        kb.startTime = time.time()

        # Parse the command line arguments
        parsed_args = cmdLineParser()
        cmdLineOptions.update(parsed_args.__dict__)

        # Initialize the configuration object
        init(cmdLineOptions)

        # Start the main controller
        start()

    except KeyboardInterrupt:
        logger.error("user aborted")
        sys.exit(1)

    except SystemExit as e:
        # This will catch clean exits from argparse (e.g., on --help or invalid arg)
        # and allow the program to terminate with the provided exit code.
        sys.exit(e.code)

    except Exception:
        # Catch all other exceptions and log them as critical errors
        message = unhandledExceptionMessage()
        logger.critical(message)
        sys.exit(1)

if __name__ == "__main__":
    main()
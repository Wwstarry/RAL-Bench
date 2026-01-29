"""Main entry point for TheFuck CLI."""

import sys
import argparse
from thefuck.command import Command
from thefuck.corrector import get_corrected_commands


def main(argv=None):
    """Main entry point for the TheFuck CLI.
    
    Args:
        argv: Command line arguments (defaults to sys.argv[1:])
        
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    parser = argparse.ArgumentParser(
        prog="thefuck",
        description="Auto-corrects your previous console command"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0"
    )
    
    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Run the corrected command without confirmation"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug output"
    )
    
    parser.add_argument(
        "command",
        nargs="*",
        help="The command to correct"
    )
    
    args = parser.parse_args(argv)
    
    if not args.command:
        parser.print_help()
        return 1
    
    # For now, just return success
    return 0


if __name__ == "__main__":
    sys.exit(main())
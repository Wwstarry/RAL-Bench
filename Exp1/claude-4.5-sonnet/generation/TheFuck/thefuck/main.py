"""Main entry point for TheFuck CLI."""

import sys
import os
from thefuck.argument_parser import Parser
from thefuck.corrector import get_corrected_commands
from thefuck.types import Command
from thefuck.utils import get_previous_command


def main(args=None):
    """Main entry point for TheFuck.
    
    Args:
        args: Command line arguments (defaults to sys.argv[1:])
        
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    parser = Parser()
    parsed_args = parser.parse(args if args is not None else sys.argv[1:])
    
    if parsed_args.help:
        parser.print_help()
        return 0
    
    if parsed_args.version:
        from thefuck import __version__
        print(f'TheFuck {__version__}')
        return 0
    
    # Get the previous command
    command = get_previous_command(parsed_args)
    
    if not command:
        print('No previous command found', file=sys.stderr)
        return 1
    
    # Get corrected commands
    corrected_commands = get_corrected_commands(command)
    
    if not corrected_commands:
        print('No fucks given', file=sys.stderr)
        return 1
    
    # In non-interactive mode or when yes flag is set, just print the first suggestion
    if parsed_args.yes or not sys.stdout.isatty():
        print(corrected_commands[0])
        return 0
    
    # Interactive mode - print the first suggestion
    print(corrected_commands[0])
    return 0
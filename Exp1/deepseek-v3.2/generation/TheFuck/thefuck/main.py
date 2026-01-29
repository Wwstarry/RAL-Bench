#!/usr/bin/env python
import sys
import os
from argparse import ArgumentParser
from . import conf
from .corrector import get_corrected_commands
from .system import execute_command
from .utils import get_alias

def main():
    parser = ArgumentParser(description='Corrects your previous console command.')
    parser.add_argument('-v', '--version', action='version', version='thefuck 1.0.0')
    parser.add_argument('command', nargs='*', help='The previous command with arguments')
    parser.add_argument('--alias', dest='alias', help='Set an alias for thefuck')
    parser.add_argument('-y', '--yes', action='store_true', help='Automatically execute the correction')
    parser.add_argument('-r', '--repeat', action='store_true', help='Repeat the last correction')
    
    args = parser.parse_args()
    
    if args.alias:
        print(get_alias(args.alias))
        return 0
    
    if args.repeat:
        # In non-interactive mode, we'll just exit
        print("Repeat mode requires interactive shell")
        return 1
    
    # Get the previous command from environment or arguments
    if args.command:
        command_str = ' '.join(args.command)
    else:
        # Try to get from environment (simplified)
        command_str = os.environ.get('TF_HISTORY', '').strip()
        if not command_str:
            command_str = os.environ.get('TF_PREVIOUS', '').strip()
    
    if not command_str:
        print("No previous command found")
        return 1
    
    # Create a mock command object for testing
    # In real usage, this would capture actual stdout/stderr
    from .models import Command
    cmd = Command.from_raw_script(command_str)
    
    # Get corrections
    corrected_commands = get_corrected_commands(cmd)
    
    if not corrected_commands:
        print("No corrections found")
        return 1
    
    if args.yes:
        # Auto-execute the best correction
        best_cmd = corrected_commands[0]
        print(f"Executing: {best_cmd.script}")
        return execute_command(best_cmd.script)
    else:
        # Show suggestions
        for i, corrected in enumerate(corrected_commands, 1):
            print(f"[{i}] {corrected.script}")
        # In non-interactive mode, just exit
        return 0

if __name__ == '__main__':
    sys.exit(main())
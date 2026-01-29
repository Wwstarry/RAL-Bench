import argparse
import os
import sys
import subprocess
from . import corrector, types, const
from .shells import get_alias
from .ui import select_command
from .settings import settings

def _get_command_from_env():
    """
    Constructs a Command object from environment variables.
    This is the primary way thefuck gets the previous command info.
    """
    script = os.environ.get('THEFUCK_COMMAND')
    if not script:
        return None

    # The reference project uses a shell logger to capture output.
    # For this implementation, we'll simulate it by re-running the command,
    # as it's a simpler and still valid approach for many cases.
    # A test harness can override this by setting THEFUCK_OUTPUT.
    if 'THEFUCK_OUTPUT' in os.environ:
        # For testing: allows providing output directly.
        # Assume stdout and stderr are combined.
        output = os.environ['THEFUCK_OUTPUT']
        return types.new_command(script, output, output)
    else:
        # Fallback: re-run the command to get its output.
        proc = subprocess.run(script, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
        return types.new_command(script, proc.stdout, proc.stderr)

def _get_command_from_args(args):
    """
    Constructs a Command object by running the command from argv.
    This is a fallback for direct CLI usage without the alias.
    """
    script = ' '.join(args)
    if not script:
        return None

    proc = subprocess.run(script, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
    return types.new_command(script, proc.stdout, proc.stderr)

def main(argv=None):
    """
    Main entry point.
    """
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(prog="thefuck", add_help=False)
    parser.add_argument(
        '--alias',
        nargs='?',
        const='fuck',
        help="Print alias for selected shell")
    parser.add_argument(
        '-y', '--yeah',
        action='store_true',
        help="Execute first suggestion without confirmation")
    parser.add_argument(
        'command',
        nargs='*',
        help="Command to correct")

    args = parser.parse_args(argv)

    if args.alias:
        print(get_alias(args.alias))
        return const.MAIN_SCENARIO_EXIT_CODE

    command = _get_command_from_env() or _get_command_from_args(args.command)

    if not command:
        parser.print_usage(sys.stderr)
        return const.NO_COMMAND_EXIT_CODE

    corrected_commands = corrector.get_corrected_commands(command)

    if not corrected_commands:
        print("No fucks given", file=sys.stderr)
        return const.NO_COMMAND_EXIT_CODE

    if args.yeah:
        selected_command = corrected_commands[0]
    else:
        selected_command = select_command(corrected_commands)

    if selected_command:
        print(selected_command.script)
        return const.MAIN_SCENARIO_EXIT_CODE
    else:
        return const.NO_COMMAND_EXIT_CODE
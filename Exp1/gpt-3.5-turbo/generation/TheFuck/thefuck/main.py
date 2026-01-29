import sys
import argparse
from thefuck.command import Command
from thefuck.rules import rules


def get_matched_rules(command: Command):
    matched = []
    for rule in rules:
        try:
            if rule.match(command):
                matched.append(rule)
        except Exception:
            # Ignore rule errors
            continue
    # Sort by priority descending
    matched.sort(key=lambda r: getattr(r, 'priority', 0), reverse=True)
    return matched


def get_suggestions(command: Command):
    matched_rules = get_matched_rules(command)
    suggestions = []
    for rule in matched_rules:
        try:
            new_cmds = rule.get_new_command(command)
            if new_cmds:
                for cmd in new_cmds:
                    if cmd not in suggestions:
                        suggestions.append(cmd)
        except Exception:
            continue
    return suggestions


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(
        description='Auto-correct your previous console command.'
    )
    parser.add_argument('command', nargs='?', help='The previous command line to fix')
    parser.add_argument('--stdout', default='', help='The stdout of the previous command')
    parser.add_argument('--stderr', default='', help='The stderr of the previous command')
    parser.add_argument('--returncode', type=int, default=0, help='The return code of the previous command')
    parser.add_argument('--yes', action='store_true', help='Automatically accept the first suggestion (non-interactive)')

    args = parser.parse_args(argv)

    if not args.command:
        print('No command provided to fix.', file=sys.stderr)
        return 1

    command = Command(args.command, args.stdout, args.stderr, args.returncode)
    suggestions = get_suggestions(command)

    if not suggestions:
        # No suggestions found
        return 1

    # Print suggestions to stdout, one per line
    for suggestion in suggestions:
        print(suggestion)

    # If --yes, exit 0 to indicate success
    return 0


if __name__ == '__main__':
    try:
        exit_code = main()
    except KeyboardInterrupt:
        exit_code = 130
    sys.exit(exit_code)
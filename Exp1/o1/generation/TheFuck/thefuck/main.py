import sys
import argparse

from thefuck.command import Command
from thefuck.rules import get_rules

def get_suggestions(command):
    """Return a list of suggested corrected commands from all matching rules."""
    suggestions = []
    for rule in get_rules():
        # Only consider the rule if enabled_by_default is True (like TheFuck)
        if getattr(rule, "enabled_by_default", True) and rule.match(command):
            new_cmds = rule.get_new_command(command)
            # Some rules may return single string or list
            if isinstance(new_cmds, str):
                new_cmds = [new_cmds]
            suggestions.extend(new_cmds)
    # Deduplicate while preserving order
    seen = set()
    final = []
    for s in suggestions:
        if s not in seen:
            final.append(s)
            seen.add(s)
    return final

def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    parser = argparse.ArgumentParser(prog="thefuck",
                                     description="Auto-correct your previous console command.")
    parser.add_argument("--command", help="The previously run command.", default="")
    parser.add_argument("--stdout", help="Captured stdout of the previous command.", default="")
    parser.add_argument("--stderr", help="Captured stderr of the previous command.", default="")
    parser.add_argument("--return_code", type=int, default=0, help="Return code of the previous command.")
    parser.add_argument("--version", action="store_true", help="Show version and exit.")
    args = parser.parse_args(argv)

    if args.version:
        from thefuck import __version__
        print(f"thefuck {__version__}")
        return 0

    # Create a Command object
    cmd = Command(script=args.command,
                  stdout=args.stdout,
                  stderr=args.stderr,
                  return_code=args.return_code)

    # Get suggestions
    suggestions = get_suggestions(cmd)

    if not suggestions:
        # No suggestions found
        return 1

    # Print all suggestions; do not run automatically in test environment
    for i, suggestion in enumerate(suggestions, start=1):
        print(f"{i}. {suggestion}")

    # Exit code 0 to indicate we found suggestions
    return 0

if __name__ == "__main__":
    sys.exit(main())
import sys
from thefuck.rules import get_rules, match_rule, apply_rule
from thefuck.command import Command


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m thefuck <previous-command>")
        return 1

    previous_command = sys.argv[1:]
    command = Command.from_args(previous_command)

    rules = get_rules()
    suggestions = []

    for rule in rules:
        if match_rule(rule, command):
            suggestions.append(apply_rule(rule, command))

    if not suggestions:
        print("No suggestions found.")
        return 1

    # Print suggestions in order of preference
    print("Suggestions:")
    for i, suggestion in enumerate(suggestions, start=1):
        print(f"{i}. {suggestion}")

    return 0
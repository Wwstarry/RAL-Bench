"""
Rule to handle "command not found" by attempting fuzzy matches to known commands.
"""
from difflib import get_close_matches

enabled_by_default = True

# A small list of "known" commands for demonstration:
KNOWN_COMMANDS = [
    "git", "ls", "cd", "cp", "mv", "rm", "mkdir", "rmdir", "touch",
    "python", "pip", "echo", "cat", "head", "tail", "grep", "find",
    "docker", "composer", "npm", "node", "yarn", "clang", "gcc"
]

def match(command):
    # If there's a "command not found" in stderr, or a typical textual clue:
    if command.return_code != 0:
        lower_err = command.stderr.lower()
        if "not found" in lower_err or "unknown command" in lower_err:
            # Then we attempt a fuzzy match
            return True
    return False

def get_new_command(command):
    script_parts = command.script.strip().split()
    if not script_parts:
        return []

    first = script_parts[0]
    rest = script_parts[1:]

    # Attempt fuzzy match for the first token
    matches = get_close_matches(first, KNOWN_COMMANDS, n=3, cutoff=0.65)
    if not matches:
        # no close match, can't fix
        return []

    new_commands = []
    for m in matches:
        new_commands.append(" ".join([m] + rest))

    return new_commands
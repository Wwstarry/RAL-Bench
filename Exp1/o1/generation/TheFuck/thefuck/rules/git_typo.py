"""
Simple rule to handle common git subcommand typos like "git brnch" => "git branch".
"""
import difflib

enabled_by_default = True

GIT_SUBCOMMANDS = [
    "add", "branch", "checkout", "clone", "commit", "diff", "fetch",
    "init", "log", "merge", "pull", "push", "rebase", "remote", "status"
]

def match(command):
    if command.return_code != 0 and command.script.startswith("git "):
        # We suspect a git subcommand was typed incorrectly.
        return True
    return False

def get_new_command(command):
    script_parts = command.script.split()
    if len(script_parts) < 2:
        return []

    # The first part is "git"
    subcmd = script_parts[1]
    rest = script_parts[2:]

    matches = difflib.get_close_matches(subcmd, GIT_SUBCOMMANDS, n=3, cutoff=0.6)
    if not matches:
        return []

    results = []
    for m in matches:
        results.append("git " + m + (" " + " ".join(rest) if rest else ""))
    return results
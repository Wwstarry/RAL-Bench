import re
from thefuck.command import Command

rules = []


def match_unknown_command(command: Command):
    # Detect "command not found" in stderr or stdout
    # Common pattern: "bash: foobar: command not found"
    # or "sh: 1: foobar: not found"
    # or "zsh: command not found: foobar"
    # or "foobar: command not found"
    patterns = [
        r'(?i)(?:bash|sh|zsh):.*: command not found',
        r'(?i)command not found',
        r'(?i)not found',
    ]
    text = command.stderr + command.stdout
    for p in patterns:
        if re.search(p, text):
            return True
    return False


def get_closest_command(cmd: str, candidates):
    # Simple heuristic: Levenshtein distance or fallback to startswith
    # Since no external libs, implement a simple Levenshtein distance
    def levenshtein(a, b):
        if len(a) < len(b):
            return levenshtein(b, a)
        if len(b) == 0:
            return len(a)
        previous_row = range(len(b) + 1)
        for i, c1 in enumerate(a):
            current_row = [i + 1]
            for j, c2 in enumerate(b):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        return previous_row[-1]

    distances = [(c, levenshtein(cmd, c)) for c in candidates]
    distances.sort(key=lambda x: (x[1], x[0]))
    if distances and distances[0][1] <= 3:
        return distances[0][0]
    return None


def get_all_commands():
    # Return a set of common commands for correction
    # Since no external data, use a static list of common commands
    return {
        'git', 'ls', 'cd', 'mkdir', 'rm', 'rmdir', 'cp', 'mv', 'python', 'pip',
        'docker', 'apt', 'apt-get', 'cat', 'echo', 'sudo', 'make', 'gcc', 'g++',
        'curl', 'wget', 'systemctl', 'service', 'ps', 'kill', 'top', 'vim', 'nano',
        'code', 'ssh', 'scp', 'man', 'head', 'tail', 'diff', 'find', 'grep', 'chmod',
        'chown', 'ping', 'ifconfig', 'ip', 'uname', 'whoami', 'env', 'export',
    }


def get_new_command(command: Command):
    parts = command.script_parts()
    if not parts:
        return []

    first = parts[0]
    if not match_unknown_command(command):
        return []

    candidates = get_all_commands()
    closest = get_closest_command(first, candidates)
    if closest and closest != first:
        new_cmd = ' '.join([closest] + parts[1:])
        return [new_cmd]
    return []


def match_missing_sudo(command: Command):
    # Detect common permission denied errors
    text = command.stderr + command.stdout
    patterns = [
        r'permission denied',
        r'operation not permitted',
        r'cannot open',
        r'could not open',
        r'not authorized',
        r'are you root',
    ]
    for p in patterns:
        if re.search(p, text, re.I):
            # Also check if command is not already prefixed with sudo
            parts = command.script_parts()
            if parts and parts[0] != 'sudo':
                return True
    return False


def get_new_command_sudo(command: Command):
    parts = command.script_parts()
    if not parts:
        return []

    if parts[0] == 'sudo':
        return []

    new_cmd = 'sudo ' + command.script
    return [new_cmd]


rules.append(
    type('RuleUnknownCommand', (), {
        'match': match_unknown_command,
        'get_new_command': get_new_command,
        'priority': 100,
        'description': 'Correct unknown command typos',
    })()
)

rules.append(
    type('RuleMissingSudo', (), {
        'match': match_missing_sudo,
        'get_new_command': get_new_command_sudo,
        'priority': 90,
        'description': 'Add sudo to commands with permission denied',
    })()
)
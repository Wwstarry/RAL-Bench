import re
from thefuck.command import Command

rules = []


def match_docker_command_not_found(command: Command):
    # Detect "docker: 'comit' is not a docker command"
    text = command.stderr + command.stdout
    if 'docker:' in text and 'is not a docker command' in text:
        return True
    return False


def get_new_command_docker_typo(command: Command):
    parts = command.script_parts()
    if len(parts) < 2:
        return []

    docker_subcommands = [
        'attach', 'build', 'commit', 'cp', 'create', 'diff', 'events', 'exec',
        'export', 'history', 'images', 'import', 'info', 'inspect', 'kill',
        'load', 'login', 'logout', 'logs', 'pause', 'port', 'ps', 'pull',
        'push', 'rename', 'restart', 'rm', 'rmi', 'run', 'save', 'search',
        'start', 'stats', 'stop', 'tag', 'top', 'unpause', 'update', 'version',
        'wait',
    ]

    wrong = parts[1]

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

    distances = [(cmd, levenshtein(wrong, cmd)) for cmd in docker_subcommands]
    distances.sort(key=lambda x: (x[1], x[0]))
    if distances and distances[0][1] <= 3:
        corrected = distances[0][0]
        new_cmd = 'docker ' + ' '.join([corrected] + parts[2:])
        return [new_cmd]
    return []


rules.append(
    type('RuleDockerCommandTypo', (), {
        'match': match_docker_command_not_found,
        'get_new_command': get_new_command_docker_typo,
        'priority': 100,
        'description': 'Fix docker subcommand typos',
    })()
)
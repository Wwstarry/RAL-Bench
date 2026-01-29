import re
from thefuck.command import Command

rules = []


def match_git_command_not_found(command: Command):
    # Detect git command errors like "git: 'comit' is not a git command"
    text = command.stderr + command.stdout
    if 'git:' in text and 'is not a git command' in text:
        return True
    return False


def get_new_command_git_typo(command: Command):
    parts = command.script_parts()
    if len(parts) < 2:
        return []

    git_subcommands = [
        'add', 'bisect', 'branch', 'checkout', 'clone', 'commit', 'diff',
        'fetch', 'grep', 'init', 'log', 'merge', 'mv', 'pull', 'push',
        'rebase', 'reset', 'rm', 'show', 'status', 'tag', 'stash',
    ]

    wrong = parts[1]
    # Find closest subcommand
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

    distances = [(cmd, levenshtein(wrong, cmd)) for cmd in git_subcommands]
    distances.sort(key=lambda x: (x[1], x[0]))
    if distances and distances[0][1] <= 3:
        corrected = distances[0][0]
        new_cmd = 'git ' + ' '.join([corrected] + parts[2:])
        return [new_cmd]
    return []


def match_git_push_without_branch(command: Command):
    # Detect "fatal: The current branch <branch> has no upstream branch."
    text = command.stderr + command.stdout
    if 'has no upstream branch' in text and 'git push' in command.script:
        return True
    return False


def get_new_command_git_push_set_upstream(command: Command):
    parts = command.script_parts()
    if len(parts) < 2:
        return []

    # Try to get current branch from error message or fallback to 'master'
    branch = 'master'
    text = command.stderr + command.stdout
    m = re.search(r"fatal: The current branch (\S+) has no upstream branch", text)
    if m:
        branch = m.group(1)

    # Compose new command with --set-upstream origin <branch>
    new_cmd = f"git push --set-upstream origin {branch}"
    return [new_cmd]


rules.append(
    type('RuleGitCommandTypo', (), {
        'match': match_git_command_not_found,
        'get_new_command': get_new_command_git_typo,
        'priority': 110,
        'description': 'Fix git subcommand typos',
    })()
)

rules.append(
    type('RuleGitPushSetUpstream', (), {
        'match': match_git_push_without_branch,
        'get_new_command': get_new_command_git_push_set_upstream,
        'priority': 105,
        'description': 'Add --set-upstream to git push when no upstream branch',
    })()
)
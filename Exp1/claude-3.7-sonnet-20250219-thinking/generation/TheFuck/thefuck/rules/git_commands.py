"""Rules for git command errors."""

import re
from thefuck.rules import register
from thefuck.types import Command
from typing import List


@register
def git_push_set_upstream(command: Command) -> List[str]:
    """Suggest git push with --set-upstream for new branches."""
    if command.script.startswith('git push') and command.return_code != 0:
        match = re.search(r'git push --set-upstream \w+ \S+', command.stderr)
        if match:
            return [match.group(0)]
    return []


@register
def git_checkout(command: Command) -> List[str]:
    """Suggest git checkout with correct branch name."""
    if command.script.startswith('git checkout') and command.return_code != 0:
        # Check for branch name suggestions
        for line in command.stderr.splitlines():
            if 'did you mean' in line.lower() or 'Did you mean' in line:
                match = re.search(r"'([^']+)'", line)
                if match:
                    branch = match.group(1)
                    parts = command.script.split()
                    for i, part in enumerate(parts):
                        if i > 0 and not part.startswith('-'):
                            parts[i] = branch
                            return [' '.join(parts)]
    return []


@register
def git_not_command(command: Command) -> List[str]:
    """Suggest corrections for mistyped git commands."""
    if ('git' in command.script and 
        command.return_code != 0 and
        "is not a git command" in command.stderr):
        
        match = re.search(r"git: '([^']+)' is not a git command", command.stderr)
        if match:
            wrong_cmd = match.group(1)
            # Common git commands
            git_commands = ['add', 'commit', 'push', 'pull', 'checkout', 'branch', 'status', 'log']
            
            # Find closest match
            closest = None
            min_dist = float('inf')
            
            for cmd in git_commands:
                dist = sum(c1 != c2 for c1, c2 in zip(wrong_cmd, cmd)) + abs(len(wrong_cmd) - len(cmd))
                if dist < min_dist:
                    min_dist = dist
                    closest = cmd
            
            if closest and min_dist <= 3:  # Allow up to 3 character differences
                return [command.script.replace(f'git {wrong_cmd}', f'git {closest}', 1)]
    
    return []
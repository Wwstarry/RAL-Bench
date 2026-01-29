from __future__ import annotations

from ..types import Command
from ..utils import shell_join

priority = 400


def match(command: Command) -> bool:
    if command.returncode == 0:
        return False
    # Only handle a very clear synthetic pattern to avoid speculative changes.
    # Pattern: git commit ... -m <msg> -a   => ... -a -m <msg>
    if len(command.args) < 6:
        return False
    if command.args[0:2] != ["git", "commit"]:
        return False
    # Need both -m and -a present, and -a appears after the -m value.
    if "-m" not in command.args or "-a" not in command.args:
        return False
    m = command.args.index("-m")
    if m == len(command.args) - 1:
        return False
    a = command.args.index("-a")
    # We only reorder if "-a" is strictly after the -m value token.
    return a > m + 1


def get_new_command(command: Command) -> str | list[str]:
    args = list(command.args)
    # Reorder: move -a to immediately after "git commit" and before -m.
    if args[0:2] != ["git", "commit"]:
        return []
    try:
        m = args.index("-m")
        a = args.index("-a")
    except ValueError:
        return []
    if m == len(args) - 1:
        return []
    if not (a > m + 1):
        return []
    # Remove -a then insert before -m.
    args.pop(a)
    # m index may have shifted if a < m; but we only handle a > m+1 so safe.
    m = args.index("-m")
    args.insert(2, "-a")
    return shell_join(args)
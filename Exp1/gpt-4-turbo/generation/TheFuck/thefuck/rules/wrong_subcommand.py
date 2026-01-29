class Rule:
    name = 'wrong_subcommand'
    priority = 200

    # Example: "git brnch" -> "git branch"
    SUBCOMMANDS = {
        'git': ['add', 'branch', 'checkout', 'clone', 'commit', 'diff', 'fetch', 'init', 'log', 'merge', 'pull', 'push', 'rebase', 'remote', 'reset', 'rm', 'show', 'status', 'tag'],
        'pip': ['install', 'uninstall', 'freeze', 'list', 'show', 'search', 'check', 'download', 'wheel', 'help'],
        'python': ['-m', '--version'],
    }

    def match(self, command):
        words = command.script.strip().split()
        if len(words) < 2:
            return False
        cmd = words[0]
        if cmd not in self.SUBCOMMANDS:
            return False
        # Only match if returncode != 0 and stderr mentions unknown subcommand
        return (
            command.returncode != 0 and
            ('unknown command' in command.stderr.lower() or
             'no such command' in command.stderr.lower() or
             'is not a git command' in command.stderr.lower())
        )

    def correct(self, command):
        import difflib
        words = command.script.strip().split()
        cmd = words[0]
        subcmd = words[1]
        candidates = self.SUBCOMMANDS.get(cmd, [])
        matches = difflib.get_close_matches(subcmd, candidates, n=2, cutoff=0.75)
        corrections = []
        for m in matches:
            corrections.append(' '.join([cmd, m] + words[2:]))
        return corrections
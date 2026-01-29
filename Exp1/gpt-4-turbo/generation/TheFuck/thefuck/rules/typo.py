import difflib

COMMON_COMMANDS = [
    'ls', 'cd', 'cat', 'echo', 'git', 'python', 'pip', 'mv', 'cp', 'rm', 'mkdir', 'rmdir',
    'touch', 'grep', 'find', 'sudo', 'head', 'tail', 'chmod', 'chown', 'man', 'pwd', 'which'
]

class Rule:
    name = 'typo'
    priority = 100

    def match(self, command):
        # Detect "command not found" in stderr
        return (
            command.returncode != 0 and
            ('command not found' in command.stderr.lower() or
             'not recognized as an internal or external command' in command.stderr.lower())
        )

    def correct(self, command):
        # Try to correct the first word (the command)
        words = command.script.strip().split()
        if not words:
            return []
        cmd = words[0]
        # Find close matches among common commands
        matches = difflib.get_close_matches(cmd, COMMON_COMMANDS, n=3, cutoff=0.75)
        corrections = []
        for m in matches:
            corrections.append(' '.join([m] + words[1:]))
        return corrections
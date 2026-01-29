class Rule:
    name = 'missing_argument'
    priority = 300

    # Example: "cp" needs at least two arguments
    REQUIRED_ARGS = {
        'cp': 2,
        'mv': 2,
        'rm': 1,
        'mkdir': 1,
        'rmdir': 1,
        'touch': 1,
        'git': 1,  # at least subcommand
        'pip': 1,
    }

    def match(self, command):
        words = command.script.strip().split()
        if not words:
            return False
        cmd = words[0]
        if cmd not in self.REQUIRED_ARGS:
            return False
        # Only match if returncode != 0 and stderr mentions missing argument
        return (
            command.returncode != 0 and
            ('missing' in command.stderr.lower() or
             'required' in command.stderr.lower() or
             'usage:' in command.stderr.lower())
        )

    def correct(self, command):
        words = command.script.strip().split()
        cmd = words[0]
        required = self.REQUIRED_ARGS.get(cmd, 1)
        # If not enough arguments, suggest a placeholder
        if len(words) < required + 1:
            missing = required + 1 - len(words)
            corrections = []
            # Add <ARG> placeholders for missing arguments
            new_words = words + [f'<ARG{i+1}>' for i in range(missing)]
            corrections.append(' '.join(new_words))
            return corrections
        return []
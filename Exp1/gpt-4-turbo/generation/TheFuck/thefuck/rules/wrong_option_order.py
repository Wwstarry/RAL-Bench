class Rule:
    name = 'wrong_option_order'
    priority = 400

    # Example: "git commit -m message" vs "git -m commit message"
    # For simplicity, only handle git and pip
    OPTION_ORDER = {
        'git': ['git', 'commit', '-m'],
        'pip': ['pip', 'install', '-r'],
    }

    def match(self, command):
        words = command.script.strip().split()
        if not words:
            return False
        cmd = words[0]
        if cmd not in self.OPTION_ORDER:
            return False
        # Only match if returncode != 0 and stderr mentions option error
        return (
            command.returncode != 0 and
            ('option' in command.stderr.lower() or
             'invalid' in command.stderr.lower() or
             'usage:' in command.stderr.lower())
        )

    def correct(self, command):
        words = command.script.strip().split()
        correct_order = self.OPTION_ORDER.get(words[0])
        if not correct_order:
            return []
        # Try to reorder options to match the expected order
        reordered = []
        used = set()
        for part in correct_order:
            if part in words:
                reordered.append(part)
                used.add(part)
        # Add remaining words
        for w in words:
            if w not in used:
                reordered.append(w)
        # Only suggest if the reordered command is different
        if reordered != words:
            return [' '.join(reordered)]
        return []
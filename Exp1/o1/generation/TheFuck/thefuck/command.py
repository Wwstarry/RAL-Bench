class Command:
    """Representation of a previously executed command."""
    def __init__(self, script, stdout, stderr, return_code):
        self.script = script
        self.stdout = stdout
        self.stderr = stderr
        self.return_code = return_code

    def __repr__(self):
        return (f"Command(script={self.script!r}, stdout={self.stdout!r}, "
                f"stderr={self.stderr!r}, return_code={self.return_code!r})")
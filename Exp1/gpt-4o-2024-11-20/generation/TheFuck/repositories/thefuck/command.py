class Command:
    def __init__(self, script, stdout="", stderr="", returncode=0):
        self.script = script
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode

    @classmethod
    def from_args(cls, args):
        """Create a Command instance from command-line arguments."""
        script = " ".join(args)
        return cls(script)

    def __repr__(self):
        return f"Command(script={self.script!r}, stdout={self.stdout!r}, stderr={self.stderr!r}, returncode={self.returncode!r})"
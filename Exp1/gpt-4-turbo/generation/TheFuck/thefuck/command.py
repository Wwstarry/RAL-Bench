class Command:
    """
    Representation of a shell command, its output, and exit code.
    """
    def __init__(self, script, stdout='', stderr='', returncode=1):
        self.script = script
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode

    def __repr__(self):
        return f"<Command script={self.script!r} rc={self.returncode}>"
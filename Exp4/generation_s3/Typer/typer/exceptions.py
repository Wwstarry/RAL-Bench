class Exit(Exception):
    """Exit the CLI early with a specific exit code."""

    def __init__(self, code: int = 0):
        super().__init__(code)
        self.exit_code = int(code)
        self.code = self.exit_code
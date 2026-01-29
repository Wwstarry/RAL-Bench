class Exit(SystemExit):
    """Exit the application with a given status code."""

    def __init__(self, code: int = 0):
        super().__init__(code)
        self.exit_code = code
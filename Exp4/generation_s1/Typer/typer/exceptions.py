class Exit(Exception):
    """
    Exception used to exit a Typer app with a specific status code.
    Compatible with Click/Typer expectations (.exit_code) and a .code alias.
    """

    def __init__(self, code: int = 0):
        super().__init__(code)
        self.exit_code = int(code)

    @property
    def code(self) -> int:
        return self.exit_code
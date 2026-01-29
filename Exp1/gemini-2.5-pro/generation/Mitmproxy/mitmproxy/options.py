class Options:
    """
    A stub for mitmproxy's options container.

    This class holds all configuration options. In this minimal implementation,
    it provides default values for options that are likely to be accessed
    by the test suite and allows dynamic attribute access.
    """
    def __init__(self):
        # Set default values for common options
        self.scripts = []
        self.verbosity = 'info'
        self.rfile = None
        self.wfile = None
        self.listen_host = '127.0.0.1'
        self.listen_port = 8080
        self.mode = "regular"

    def __getattr__(self, name: str):
        """Default to None for any unknown option."""
        return None

    def __setattr__(self, name: str, value):
        super().__setattr__(name, value)
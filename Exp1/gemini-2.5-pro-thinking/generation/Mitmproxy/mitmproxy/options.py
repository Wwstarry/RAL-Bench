class Options:
    """
    A minimal, safe-to-evaluate placeholder for mitmproxy's options store.
    """
    def __init__(self, **kwargs):
        self.update(**kwargs)

    def __getattr__(self, name):
        # Provide a default value for any requested option to avoid errors.
        return None

    def __setattr__(self, name, value):
        super().__setattr__(name, value)

    def update(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
class AttribDict(dict):
    """
    Small dict subclass with attribute access (similar to sqlmap's AttribDict).
    """
    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError as e:
            raise AttributeError(item) from e

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, item):
        try:
            del self[item]
        except KeyError as e:
            raise AttributeError(item) from e


# Global containers (expected by tests/importers)
cmdLineOptions = None  # raw parsed argparse Namespace (or compatible)
conf = AttribDict()
kb = AttribDict()
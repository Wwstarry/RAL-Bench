class AttribDict(dict):
    """
    Dictionary subclass that allows attribute access to keys.
    """
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        self[name] = value

# Global data structures
cmdLineOptions = AttribDict()
conf = AttribDict()
kb = AttribDict()
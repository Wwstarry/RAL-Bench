class AttribDict(dict):
    """
    Dictionary that allows attribute-style access.
    This is a common pattern in projects like sqlmap to simplify access
    to configuration and state objects.
    e.g., conf.url instead of conf['url']
    """
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            # Return None for non-existent attributes to prevent crashes
            # on optional parameters, mimicking sqlmap's lenient access.
            return None

    def __setattr__(self, name, value):
        self[name] = value

# Globally shared objects for runtime state
cmdLineOptions = AttribDict()
conf = AttribDict()
kb = AttribDict()
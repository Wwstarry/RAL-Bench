def hashkey(*args, **kwargs):
    """
    Default key function for cached decorator. Creates
    a key based on positional and keyword arguments.
    """
    return (args, frozenset(kwargs.items()))

def methodkey(self, *args, **kwargs):
    """
    Default key function for cachedmethod decorator.
    Includes an identifier for 'self' plus arguments.
    """
    return (id(self), args, frozenset(kwargs.items()))
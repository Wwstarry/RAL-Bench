def _make_key(args, kwargs, typed):
    """Make a cache key from function arguments."""
    key = args
    if kwargs:
        key += tuple(sorted(kwargs.items()))
    if typed:
        key += tuple(type(v) for v in args)
        if kwargs:
            key += tuple(type(v) for v in kwargs.values())
    return key


def hashkey(*args, **kwargs):
    """
    Return a cache key for the specified arguments.
    
    This is the default key function used by the cached decorators.
    """
    return _make_key(args, kwargs, typed=False)


def typedkey(*args, **kwargs):
    """Return a cache key that includes argument types."""
    return _make_key(args, kwargs, typed=True)
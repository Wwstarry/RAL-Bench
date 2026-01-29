import collections.abc

def hashkey(*args, **kwargs):
    """Return a cache key for the given arguments."""
    if not kwargs:
        return args
    items = tuple(sorted(kwargs.items()))
    return args + items

def typedkey(*args, **kwargs):
    """Return a cache key including argument types."""
    key = hashkey(*args, **kwargs)
    types = tuple(type(arg) for arg in args)
    if kwargs:
        types += tuple(type(v) for k, v in sorted(kwargs.items()))
    return key + types

def deepkey(*args, **kwargs):
    """Return a cache key that recursively expands arguments."""
    def expand(obj):
        if isinstance(obj, dict):
            return tuple(sorted((k, expand(v)) for k, v in obj.items()))
        elif isinstance(obj, (list, tuple)):
            return tuple(expand(v) for v in obj)
        elif isinstance(obj, set):
            return tuple(sorted(expand(v) for v in obj))
        return obj
    key = tuple(expand(arg) for arg in args)
    if kwargs:
        key += tuple(sorted((k, expand(v)) for k, v in kwargs.items()))
    return key
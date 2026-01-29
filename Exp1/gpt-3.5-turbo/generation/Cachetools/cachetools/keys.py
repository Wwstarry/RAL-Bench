def hashkey(*args, **kwargs):
    """Create a cache key from function arguments."""
    key = args
    if kwargs:
        # Sort kwargs by key to ensure consistent ordering
        items = tuple(sorted(kwargs.items()))
        key += items
    return key